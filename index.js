const backToTop = document.getElementById("backToTop");

window.onscroll = function () {
   if (
     document.body.scrollTop > 100 ||
     document.documentElement.scrollTop > 100
   ) {
     backToTopButton.style.display = "block";
   } else {
     backToTopButton.style.display = "none";
   }
};
