const headerEl = document.querySelector('.navigation');
const menuStateEl = document.getElementById('menu-state');
const languageSwitcherEl = document.querySelector('.language-switcher');
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

if (languageSwitcherEl) {
  const currentFlagEl = languageSwitcherEl.querySelector('.language-current');
  const summaryEl = languageSwitcherEl.querySelector('summary');
  const languageLinks = languageSwitcherEl.querySelectorAll('[data-language-link]');
  const isEnglishPage = window.location.pathname === '/en' || window.location.pathname.startsWith('/en/');
  const swedishPath = isEnglishPage ? window.location.pathname.replace(/^\/en(?=\/|$)/, '') || '/' : window.location.pathname;
  const englishPath = isEnglishPage ? window.location.pathname : `/en${window.location.pathname === '/' ? '/' : window.location.pathname}`;
  const suffix = `${window.location.search}${window.location.hash}`;
  const paths = {
    sv: `${swedishPath}${suffix}`,
    en: `${englishPath}${suffix}`,
  };
  const currentLanguage = isEnglishPage ? 'en' : 'sv';

  if (currentFlagEl) {
    currentFlagEl.classList.remove('language-flag-sv', 'language-flag-en');
    currentFlagEl.classList.add(`language-flag-${currentLanguage}`);
  }

  if (summaryEl) {
    summaryEl.setAttribute('aria-label', currentLanguage === 'en' ? 'Choose language' : 'Välj språk');
  }

  languageLinks.forEach((link) => {
    const language = link.dataset.languageLink;
    if (!paths[language]) return;

    link.href = paths[language];
    if (language === currentLanguage) {
      link.setAttribute('aria-current', 'page');
    } else {
      link.removeAttribute('aria-current');
    }
  });

  document.addEventListener('click', (event) => {
    if (!languageSwitcherEl.open || !(event.target instanceof Node)) return;
    if (!languageSwitcherEl.contains(event.target)) {
      languageSwitcherEl.open = false;
    }
  });
}

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
