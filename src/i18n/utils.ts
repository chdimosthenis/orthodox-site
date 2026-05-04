import { ui, defaultLang, type Lang, type UIKey } from './ui';

export function getLangFromUrl(url: URL): Lang {
  const [, segment] = url.pathname.split('/');
  if (segment && segment in ui) return segment as Lang;
  return defaultLang;
}

export function useTranslations(lang: Lang) {
  return function t(key: UIKey): string {
    return ui[lang][key] ?? ui[defaultLang][key];
  };
}

/** Build a path scoped to the active locale. Default lang has no prefix. */
export function getLocalizedPath(path: string, lang: Lang): string {
  if (lang === defaultLang) return path;
  if (path === '/') return `/${lang}/`;
  return `/${lang}${path}`;
}

/** Given the current URL and the target lang, build the equivalent URL in the other locale. */
export function getAlternateUrl(url: URL, targetLang: Lang): string {
  let path = url.pathname;
  // Strip current /xx prefix if any
  for (const code of Object.keys(ui)) {
    const prefix = `/${code}`;
    if (path === prefix || path === `${prefix}/`) {
      path = '/';
      break;
    }
    if (path.startsWith(`${prefix}/`)) {
      path = path.slice(prefix.length);
      break;
    }
  }
  return getLocalizedPath(path, targetLang);
}
