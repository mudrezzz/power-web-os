import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { resources } from './i18nResources';

export const supportedLocales = ['en', 'ru'] as const;
export type SupportedLocale = (typeof supportedLocales)[number];

export const defaultLocale: SupportedLocale = 'en';
export const localeStorageKey = 'power-web-os-locale';

function getInitialLocale(): SupportedLocale {
  const stored = window.localStorage.getItem(localeStorageKey);
  return supportedLocales.includes(stored as SupportedLocale) ? (stored as SupportedLocale) : defaultLocale;
}

void i18n.use(initReactI18next).init({
  fallbackLng: defaultLocale,
  interpolation: {
    escapeValue: false,
  },
  lng: getInitialLocale(),
  resources,
});

export { i18n };
