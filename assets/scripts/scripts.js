const headerEl = document.querySelector('.navigation');

window.addEventListener('scroll', () => {
  if (window.scrollY > 100) {
    headerEl.classList.add('header-scrolled');
  } else if (window.scrollY <= 100) {
    headerEl.classList.remove('header-scrolled');
  }
});

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
