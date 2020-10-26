/*
Template Name: Admiria - Responsive Bootstrap 4 Admin Dashboard
Author: Themesbrand
Website: https://themesbrand.com/
Contact: themesbrand@gmail.com
File: Animate
*/

function testAnim(x) {
    $('#animationSandbox').removeClass().addClass(x + ' animated').one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
        $(this).removeClass();
    });
};

$(document).ready(function() {
    $('.js--triggerAnimation').click(function(e) {
        e.preventDefault();
        var anim = $('.js--animations').val();
        testAnim(anim);
    });

    $('.js--animations').change(function() {
        var anim = $(this).val();
        testAnim(anim);
    });
});
