const headerEl = document.querySelector('.navigation');
const menuStateEl = document.getElementById('menu-state');
const MOBILE_BREAKPOINT = 640;

const resetMenuStateOnDesktop = () => {
  if (menuStateEl && window.innerWidth > MOBILE_BREAKPOINT) {
    menuStateEl.checked = false;
  }
};

window.addEventListener('scroll', () => {
  if (window.scrollY > 100) {
    headerEl.classList.add('header-scrolled');
  } else if (window.scrollY <= 100) {
    headerEl.classList.remove('header-scrolled');
  }
});

window.addEventListener('resize', resetMenuStateOnDesktop);
window.addEventListener('pageshow', resetMenuStateOnDesktop);
resetMenuStateOnDesktop();

const accordionItems = document.querySelectorAll('.accordion-item');

accordionItems.forEach((item) =>
  item.addEventListener('click', () => {
    const isItemOpen = item.classList.contains('open');
    accordionItems.forEach((item) => item.classList.remove('open'));
    if (!isItemOpen) {
      item.classList.toggle('open');
    }
  })
);
