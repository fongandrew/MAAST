$(function(){
   
   var $container = $('#container');
   
   $container.isotope({
     itemSelector: '.element',
	 columnWidth: 200
   });
   
 });

  var $container = $('#container');

  // remove item if clicked
  $container.delegate( '.element', 'click', function(){
    $container.isotope( 'remove', $(this) );
  });

