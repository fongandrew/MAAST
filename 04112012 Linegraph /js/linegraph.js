// JavaScript Document



var chart;
$(document).ready(function() {
	chart = new Highcharts.Chart({
		chart: {
			renderTo: 'container',
			type: 'spline',
			
		},
		title: {
			text: 'Your Emails with Jenny'
		},
		subtitle: {
			text: ''
		},
		xAxis: {
			

                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',

                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
		},
		yAxis: {
			title: {
				text: 'emails'
			}
		},
		tooltip: {
			formatter: function() {
					return ''+
					this.y;
			}
		},
		legend: {
			layout: 'horizontal',
			align: 'center',
			verticalAlign: 'top',
			x: 30,
			y: 30,
			floating: true,
			backgroundColor: '#FFFFFF',
			borderWidth: 1
		},
		plotOptions: {
			scatter: {
				marker: {
					radius: 5,
					states: {
						hover: {
							enabled: true,
							lineColor: 'rgb(100,100,100)'
						}
					}
				},
				states: {
					hover: {
						marker: {
							enabled: false
						}
					}
				}
			}
		},
		series: [{
			name: '2006',
			data: [["january",1316],
				  ["february",994],
				  ["march",218],
				  ["april",588],
				  ["may",636],
				  ["june",363],
				  ["july",1203],
				  ["august",514],
				  ["september",1277],
				  ["october",1034],
				  ["november",1033],
				  ["december",961],]

		}, {
			name: '2007',
			data: [ ["january",254],
					["february",1697],
					["march",1238],
					["april",824],
					["may",661],
					["june",1099],
					["july",1443],
					["august",1285],
					["september",1320],
					["october",1568],
					["november",625],
					["december",869]]
		}, {
			name: '2008',
			data: [  ["january",1434],
					["february",412],
					["march",1394],
					["april",1142],
					["may",960],
					["june",390],
					["july",640],
					["august",1112],
					["september",571],
					["october",1602],
					["november",102],
					["december",121]]
		}, {
			name: '2009',
			data: [ ["january",1493],
					["february",460],
					["march",703],
					["april",233],
					["may",950],
					["june",1349],
					["july",438],
					["august",1008],
					["september",928],
					["october",937],
					["november",1268],
					["december",630]]
		}, {
			name: '2010',
			data: [["january",254],
					["february",1697],
					["march",1238],
					["april",824],
					["may",661],
					["june",1099],
					["july",1443],
					["august",1285],
					["september",1320],
					["october",1568],
					["november",625],
					["december",869],]
		}, {
			name: '2011',
			data: [ ["january",1530],
					["february",1020],
					["march",1362],
					["april",1513],
					["may",525],
					["june",503],
					["july",1340],
					["august",1256],
					["september",1283],
					["october",847],
					["november",1224],
					["december",723]]
		}, {
			name: '2012',
			data: [ ["january",585],
					["february",1052],
					["march",1047],
					["april",1159],
					["may",1216]]
		}]
	});
});

