/* Theme Name: Admiria - Responsive Bootstrap 4 Admin Dashboard & Frontend
   Author: Themesbrand
   File Description:Main JS file of the template
*/


(function ($) {

    'use strict';

    function initNavbar() {
        $('.navbar-nav a').bind('click', function(event) {
          var $anchor = $(this);
          $('html, body').stop().animate({
              scrollTop: $($anchor.attr('href')).offset().top - 0
          }, 1500, 'easeInOutExpo');
          event.preventDefault();
      });
    }
    function initSticky() {
        $(window).on('load', function() {
            $(".sticky").sticky({
              topSpacing: 0
          });
        });
    }
    function initMagnificPopoup() {
        $('.image-popup').magnificPopup({
            type: 'image',
            closeOnContentClick: true,
            mainClass: 'mfp-fade',
            gallery: {
                enabled: true,
                navigateByImgClick: true,
                preload: [0,1] // Will preload 0 - before current, and 1 after the current image
            }
        });
    }
    
    function init() {
        initNavbar();
        initSticky();
        initMagnificPopoup();
    }

    init();

})(jQuery);

