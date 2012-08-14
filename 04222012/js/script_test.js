$(function(){
   
  // for homepage

  // if a button with id "getstuff" exists, then do the following
  if ($('button#getStuff').length) {
  	$('button#getStuff').click( function() {
	    
	    var email = $('input#askEmailTextBox').val();
	    var modalContent = "DeloreanMail is asking for some information from your Google account <strong>" +
 	    	email + "</strong> including your email address, contacts, and email archive. " +
			"DeloreanMail takes <a href='#'>your privacy</a> seriously and will never share any of " +
			"your personal information.";
	   
		$('p#modal-content').html(modalContent);
		
		// display popup
		$('#googleAllowPopup').show();
		$('#googleAllowPopup').modal();

	   });
   }

  // for infographic controls (defaultInfographic.html)
  
  // set up isotope
  if ($('#container').length) {   
   $('#container').isotope({
     itemSelector: '.element',
	 masonry: {
		columnWidth: 320
	 }
   });
   
  }
     
   // print: brings up printing menu
   if($('a.printInfoGraphic').length) {
		$('a.printInfoGraphic').click( function() {
			window.print();
		});
	
	}
	
	// edit: makes elements removable
	if($('a.editInfoGraphic').length) {
		$('a.editInfoGraphic').click( function() {
		
		// change control text
		$('a.editInfoGraphic').hide();
		$('a.stopEditingInfoGraphic').show();
		
		// display close icon for elements
		$(".closeButton").show();
		
		// enable elements to be removed by clicking on them
		var $container = $('#container');
		// remove item if clicked
		  $('#container').delegate( '.element', 'click', setRemoveItemFromContainer);
		});

	}
	
	// stop editing: makes element not removable
	if($('a.stopEditingInfoGraphic').length) {
		$('a.stopEditingInfoGraphic').click( function() {
		
		// change control text
		$('a.stopEditingInfoGraphic').hide();
		$('a.editInfoGraphic').show();
		
		// hide close icon
		$(".closeButton").hide();	
		
		// prevent delegates from being removed
		var $container = $('#container');
		// remove item if clicked
		  $container.undelegate( '.element', 'click', setRemoveItemFromContainer);
		});

	}
	
	if($('a#shareInfoGraphicOnFB').length) {
		$('a#shareInfoGraphicOnFB').click( function() {
			alert('Your infographic was just sent to Jenny!')
		});
	}

});

// infographic page: function that is used for infographic: removes items
function setRemoveItemFromContainer() {
	$('#container').isotope( 'remove', $(this) );
}

// hhome page: if someone clicks on "allow" on Google popup, this displays the progress bar and loads the next page
function allowGoogle() {

	$('#googleAllowPopup').modal('hide');

	//text that is displayed once email is submitted
	$('h1#emailFormTitle').html("Thanks!");
	$('p#emailFormDescription').html("Please wait a few moments while your contacts are being mined.");

	// show progress bar
	$('#loadingStatus').show();

	// hide input box and text box
	$('input#askEmailTextBox').hide();
	$('button#getStuff').hide();

	// code that automatically simulates progress bar animation
	width = 0;
	increment = 10;
	// page is loaded automatically to contacts.html
	setInterval(function() {
		width += increment
		$('#loadingStatusProgressBar').css('width', width + '%')

		// once progress bar is complete, move to next page
		if(width >= 100) {
			window.location.replace("contacts.html");
		}
	}, 300)

}