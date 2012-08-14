//bar graph setting
var barWidth = 15;
var width = 900;
var height = 180;
var data = [];
var count_to_from = [];

//padding below bar1
var padding_bottom = "70px";

var text_font_size = "22px";
var text_font_family = "Colaborate";

//bar 2
var bar2_y = "25px";

var last_year = -1;
var last_month = -1;

function setData(user_data) {
  //if user data doesn't start january.. fill out missing months
  var temp_data = [];
  if(user_data[0].Month != 1 )
  {
    var i_month = 1;

    var i = 1;
    
    while(i_month < user_data[0].Month)
    {
      temp_data.push({"From":0, "Month": i_month, "To":0, "Year": user_data[0].Year});
      i_month++;
    }
    
    for(i in user_data)
    {
      temp_data.push(user_data[i]);
      last_year = user_data[i].Year;
      last_month = user_data[i].Month;
      count_to_from.push(user_data[i].To);
      count_to_from.push(user_data[i].From);
    }
  }
  
  data = temp_data;
  
  //set bar width
  if((barWidth+1) * data.length > width )
  {
    barWidth = Math.round(width/data.length)-1.5;
  }

}

function drawBarGraph(){
  if(width == 0)
    alert("data hasn't been set!");
    
  var x = d3.scale.linear().domain([0, data.length]).range([(width/2)-((barWidth+1) * data.length/2), (width/2)+((barWidth+1) * data.length/2)]);
//  var y = d3.scale.linear().domain([0, d3.max(data, function(datum) { return datum.To; })]).rangeRound([0, height*0.8]);
  var y = d3.scale.linear().domain([0, d3.max(count_to_from)]).rangeRound([0, height*0.8]);
  
  //bar1
  var bar1 = d3.select("#bar_graph")
    .append("svg:svg")
    .attr("width", width)
    .attr("height", height)
    .style("padding-bottom", padding_bottom);

  //text (From xxx to yyy)
  /*
  bar1.append("svg:text").
    attr("x", 0).
    attr("y", 30).
    style("font-size", text_font_size).
    style("font-family", "Colaborate").
    style("fill", "#276654").
    text("From Ariel to Jenny");
  */
  //bar graph (To)
  var bar_graph = bar1.selectAll("rect")
    .data(data)
    .enter()
    .append("svg:rect")
    .attr("x", function(datum, index) { return x(index); })
    .attr("y", function(datum) {return height - y(datum.To); })
    .attr("rx", 3)
    .attr("ry", 3)
    .attr("height", function(datum) { return y(datum.To); })
    .attr("width", barWidth)
    .attr("fill", function(d,i) {
    		if((d.Year%2) == 0){
    			return "#00A872";}
    		else{
    			return "#F2BC1B";      		  
    		}
    });


    bar1.selectAll("text").data(data).enter().append("svg:text").
      attr("x", function(datum, index) { return x(index) + barWidth; }).
      attr("y", function(datum) {return height - y(datum.To);} ).
      attr("dx", -barWidth/2).
      attr("dy", "1em").
      attr("text-anchor", "middle").
      text(function(datum) { if(parseInt(datum.To) > 0){return datum.To;}}).
      attr("fill", "white").
      attr("style", "font-size:10; font-family: Helvetica, sans-serif");

  //Month Axis
    bar1.selectAll("text.mAxis").data(data).enter().append("svg:text").
      attr("x", function(datum, index) { return x(index) + barWidth; }).
      attr("y", height).
      attr("dx", -barWidth/2).
      attr("dy", 5).
      attr("text-anchor", "Start").
      attr("style", "font-size: 10; font-family: Helvetica, sans-serif;").   
      text(function(datum) { 
        if(datum.Month == 1){return "jan";}
        else if(datum.Month == 5){return "may";}
        else if(datum.Month == 9){return "sept";}}).
      attr("transform", function(datum, index){return "rotate(270 "+ (x(index)+17) + " " + (height+13) + ")";}).
      attr("fill", "black").
      attr("class", "mAxis");  

  //Year Axis  
    bar1.selectAll("text.yAxis").data(data).enter().append("svg:text").
      attr("x", function(datum, index) {
        if(datum.Year == last_year && last_month < 8){ return x(index) + barWidth*2;}
        else{return x(index) + barWidth*7;} }).
      attr("y", height+50).
      attr("dx", -barWidth/2).
      attr("dy", 5).
      attr("text-anchor", "middle").
      attr("style", "font-size: 18; font-family: colaborate, sans-serif;").  
      style("font-family", "BebasNeue").   
      style("font-size", "34px").
      style("fill", "gray"). 
      text(function(datum) { 
        if(datum.Month == 1){return datum.Year;}}).
      attr("transform", "translate(0, 5)").
      attr("fill", "black").
      attr("class", "mAxis");  


  /***** SECOND GRAPH  ***************/
  var x2 = d3.scale.linear().domain([0, data.length]).range([(width/2)-((barWidth+1) * data.length/2), (width/2)+((barWidth+1) * data.length/2)]);
//  var y2 = d3.scale.linear().domain([0, d3.max(data, function(datum) { return datum.From; })]).rangeRound([0, height*0.8]);
  var y2 = d3.scale.linear().domain([0, d3.max(count_to_from)]).rangeRound([0, height*0.8]);  
  
  var bar2 = d3.select("#bar_graph").append("svg:svg").
      attr("width", width).
      attr("height", height);

  //text (From xxx to yyy)
  /*
  bar2.append("svg:text").
    attr("x", 0).
    attr("y", 180).
    style("font-size", text_font_size).
    style("font-family", text_font_family).
    style("fill", "#276654").
    text("From Jenny to Ariel");
*/
    //bar graph (From)
    bar2.selectAll("rect").
      data(data).
      enter().
      append("svg:rect").
      attr("x", function(datum, index) { return x2(index); }).
      attr("y", bar2_y).
      attr("rx", 3).
      attr("ry", 3).
      attr("height", function(datum) { return y2(datum.From); }).
      attr("width", barWidth).
      attr("fill", function(d,i) {
      		if((d.Year%2) == 0){
      			return "#8CCC90";}
      		else{
      			return "#F1D13F";      		  
      		}
        });


    bar2.selectAll("text").data(data).enter().append("svg:text").
      attr("x", function(datum, index) { return x2(index) + barWidth/2; }).
      attr("y", function(datum) { return (y2(datum.From)+parseInt(bar2_y)-2); }).
//      attr("dx", -barWidth/2).
//      attr("dy", "1em").
      attr("text-anchor", "middle").
      text(function(datum) {if(parseInt(datum.From) > 0){return datum.From;}}).
      attr("fill", "white").
      attr("style", "font-size: 10; font-family: Helvetica, sans-serif");  

    //Month Axis for bar 2 graph
      bar2.selectAll("text.mAxis").data(data).enter().append("svg:text").
        attr("x", function(datum, index) { return x2(index) + barWidth; }).
        attr("y", bar2_y).
        attr("text-anchor", "End").
        attr("style", "font-size: 10; font-family: Helvetica, sans-serif;").   
        text(function(datum) { 
          if(datum.Month == 1){return "jan";}
          else if(datum.Month == 5){return "may";}
          else if(datum.Month == 9){return "sept";}}).
        attr("transform", function(datum, index){return "rotate(90 "+ (x2(index)+10) + " " + (parseInt(bar2_y)-7) + ")";}).
        attr("fill", "black").
        attr("class", "mAxis");  


}
