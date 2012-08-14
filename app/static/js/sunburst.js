var max_num_emails = 0;
var data_display_width = 500;
var data_display_height = 600;
var outer_radius_ratio = 150;
var num_emails_per_hour = [];

function setData(incoming_data, n){
  num_emails_per_hour = incoming_data;
  var i=0;
  while(i < (n+6)) //offset by 6 because the first hour time period starts at 6 AM
  {
    var hour = num_emails_per_hour.shift();    
    num_emails_per_hour.push(hour);
    i++;
  }
  max_num_emails = Math.max.apply(null, incoming_data)
}

/** Clear the data display. */
function clearDataDisplay() {
    var display = d3.select("#sunBurst");
    display.selectAll("svg").remove();
    display.selectAll("div").remove();
}

/** Compute a partition of a domain with a "selected" item.
*** @param low The domain's lowest value. (pre: low < high)
*** @param high The domain's highest value. (pre: low < high)
*** @param div The number of partititions. (pre: div > 1)
*** @param index The index for the selection. If the index is negative,
***              than an equi-partition is performed. 
***              (pre: index < div)
*** @param inflation This factor magnifies the selection. (e.g. 20%
***                  increase in size implies inflation = 1.2)
***                  (pre: inflation > 0)
*** @return An array of pairs, where each pair is a region in the
***         partition, everything ordered from low to high. */
function computePartition(low, high, div, index, inflation) {
    // Setup.
    var delta = high - low;
    var reg_width = delta / div;
    var big_width = (index < 0) ? reg_width : inflation * reg_width;
    reg_width *= (delta - big_width) / (delta - reg_width);
    index = (index < 0) ? 0 : index;

    // Partition.
    var data = new Array(div);
    var anchor = reg_width * index + low;
    data[index] = [ anchor, anchor + big_width ];
    for (var i = index + 1; i < div; i++) {
        anchor = data[i - 1][1];
        data[i] = [ anchor, anchor + reg_width ];
    }
    for (var i = index - 1; i >= 0; i--) {
        anchor = data[i + 1][0];
        data[i] = [ anchor - reg_width, anchor ];
    }

    return data;
}

/** Create an arc-radial svg chunk.
*** @param index The index for the selected chunk. 
***              (assert 0 < index < 16) 
*** @param r1 The inner-radius for the chunk.
*** @param r2 The outer-radius for the chunk.
*** @return The created svg chunk. */
function createChunk(index, r1) {
    // Setup with partition of [0, 2 * PI].
    var inflation = 1.1;
   var chunk_count = 24;
    var partition = 
        computePartition(0, 2 * Math.PI, chunk_count, index, inflation);

    // Create closures for anonymous functions.
    function startAngleClosure(list) {
        return function (d, i) { return list[i][0]; };
    }
    function endAngleClosure(list) {
        return function (d, i) { return list[i][1]; };
    }
    function outerRadiusClosure(r1) {
        return function (d, i) { // Create the chunk. 
          return r1 + Math.ceil(d/max_num_emails*outer_radius_ratio); };
    }
    
    var chunk = d3.svg.arc()
        .startAngle(startAngleClosure(partition))
        .endAngle(endAngleClosure(partition))
        .innerRadius(r1)
        .outerRadius(outerRadiusClosure(r1));

    return chunk;
}

/** Start the loading widget. */
function loadStart() {
    // Setup.
    var size = Math.min(data_display_width, data_display_height);
    var center = "(" + size / 2 + ", " + size / 2 + ")";
    var inner_radius = 75;
    loading = true;
    clearDataDisplay();

    // Shape templates.
    // outer circle
    var outer_chunk = createChunk(-1, inner_radius);
    
    // Construct the graphics for the loader.
    var loader = d3.select("#sunBurst").append("svg")
        .attr("class", "loader")
        .attr("width", size)
        .attr("height", size)
        .append("g")
            .attr("transform", "translate" + center);

    //draw the outer circle
    var chunks = loader.selectAll("path")
        .data(num_emails_per_hour) //load the data
        .enter().append("path")
            .attr("class", "chunk")
            .attr("d", outer_chunk)
            .style("fill", function(d,i) { //am:1, pm:2
                if(i<12)
                {
                  return ("#F2BC1B");
                }else{
                  return ("#00A872");
                }
              });
    
    loader.selectAll("text").data(num_emails_per_hour)
    .enter().append("svg:text")
      .attr("x", function(d,i) {
          var x_margin=0;
          if(i>=12 & i<18){
            x_margin = -25;
          }
          if(i>=18 & i<24){
            x_margin = -25;
          }
          var this_radius = inner_radius + Math.ceil(d/max_num_emails*outer_radius_ratio);
          return this_radius*Math.cos(i*Math.PI/12-Math.PI/2+Math.PI/24)+x_margin;
        })
      .attr("y", function(d,i) {
          var y_margin=0;
          var this_radius = inner_radius + Math.ceil(d/max_num_emails*outer_radius_ratio);
          if(i>=6 & i<12){
            y_margin = 15;
          }
          if(i>=12 & i<18){
            y_margin = 10;
          }
          if(i>=18 & i<24){
            y_margin = -5;
          }              
          return this_radius*Math.sin(i*Math.PI/12-Math.PI/2+Math.PI/24)+y_margin;
        })
      .text(function(d) {return d;})
      .style("font-size",12)
      .style("font-family", "BebasNeue");
      
    //draw the inner circle
    var inner_circle = loader.append("svg:image")
        .attr("xlink:href", "/static/img/sunburst_center_150.png")
        .attr("x", inner_radius*-1)
        .attr("y", inner_radius*-1)
        .attr("width", inner_radius*2)
        .attr("height", inner_radius*2)
//        var circle = loader.append("path")
//            .attr("d", inner_circle);

    var legend = loader.append("svg:image")
        .attr("xlink:href", "/static/img/sunburst_ledgend_140X40.png")
        .attr("x", 110)
        .attr("y", -200)
        .attr("width", 140)
        .attr("height", 40);
    // Start transition-callback loop.
    //loadContinue(r2, r3);
}