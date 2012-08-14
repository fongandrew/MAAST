/* Inspired by Lee Byron's test data generator. */
function stream_layers(n, m, o) {
  if (arguments.length < 3) o = 0; 
  function bump(a) {
    var x = 1 / (.1 + Math.random()),
        y = 1 * Math.random(),
        z = 10 / (.1 + Math.random());
    for (var i = 0; i < m; i++) {
      var w = (i / m - y) * z;
      a[i] += x * Math.exp(-w * w);
    }
  }
  return d3.range(n).map(function() {
      var a = [], i;
      for (i = 0; i < m; i++) a[i] = 1;
      for (i = 0; i < 5; i++) bump(a);
      return a.map(stream_index);
    });
}

/* Another layer generator using gamma distributions. */
function stream_waves(n, m) {
  return d3.range(n).map(function(i) {
    return d3.range(m).map(function(j) {
        var x = 20 * j / m - i / 3;
        return 2 * x * Math.exp(-.5 * x);
      }).map(stream_index);
    });
}

function stream_index(d, i) {
  return {x: i, y: Math.max(0, d)};
}

/*
data = 
[{"Year":2008,"Month":4,"From":442,"To":473},
{"Year":2008,"Month":5,"From":1191,"To":1319},
{"Year":2008,"Month":6,"From":1174,"To":1312},
{"Year":2008,"Month":7,"From":635,"To":688},
{"Year":2008,"Month":8,"From":858,"To":1222},
{"Year":2008,"Month":9,"From":980,"To":1064},
{"Year":2008,"Month":10,"From":1248,"To":1398},
{"Year":2008,"Month":11,"From":773,"To":1098},
{"Year":2008,"Month":12,"From":506,"To":815},
{"Year":2009,"Month":1,"From":516,"To":916},
{"Year":2009,"Month":2,"From":544,"To":913},
{"Year":2009,"Month":3,"From":827,"To":1266},
{"Year":2009,"Month":4,"From":932,"To":1351},
{"Year":2009,"Month":5,"From":1002,"To":1236},
{"Year":2009,"Month":6,"From":734,"To":902},
{"Year":2009,"Month":7,"From":729,"To":832},
{"Year":2009,"Month":8,"From":778,"To":861},
{"Year":2009,"Month":9,"From":1096,"To":1249},
{"Year":2009,"Month":10,"From":1251,"To":1407},
{"Year":2009,"Month":11,"From":1518,"To":1721},
{"Year":2009,"Month":12,"From":1085,"To":1272},
{"Year":2010,"Month":1,"From":1381,"To":1547},
{"Year":2010,"Month":2,"From":1203,"To":1376},
{"Year":2010,"Month":3,"From":1368,"To":1545},
{"Year":2010,"Month":4,"From":1427,"To":1606},
{"Year":2010,"Month":5,"From":845,"To":970},
{"Year":2010,"Month":6,"From":994,"To":1120},
{"Year":2010,"Month":7,"From":909,"To":1094},
{"Year":2010,"Month":8,"From":1397,"To":1557},
{"Year":2010,"Month":9,"From":1889,"To":2062},
{"Year":2010,"Month":10,"From":1900,"To":2087},
{"Year":2010,"Month":11,"From":1606,"To":1758},
{"Year":2010,"Month":12,"From":865,"To":967},
{"Year":2011,"Month":1,"From":1558,"To":1745},
{"Year":2011,"Month":2,"From":1411,"To":1539},
{"Year":2011,"Month":3,"From":1630,"To":1733},
{"Year":2011,"Month":4,"From":1854,"To":1981},
{"Year":2011,"Month":5,"From":918,"To":1023},
{"Year":2011,"Month":6,"From":755,"To":812},
{"Year":2011,"Month":7,"From":858,"To":912},
{"Year":2011,"Month":8,"From":1206,"To":1305},
{"Year":2011,"Month":9,"From":1715,"To":1882},
{"Year":2011,"Month":10,"From":1655,"To":1810},
{"Year":2011,"Month":11,"From":1612,"To":1828},
{"Year":2011,"Month":12,"From":1054,"To":1218},
{"Year":2012,"Month":1,"From":1674,"To":1810},
{"Year":2012,"Month":2,"From":1492,"To":1606},
{"Year":2012,"Month":3,"From":1676,"To":1783},
{"Year":2012,"Month":4,"From":885,"To":930}]
*/