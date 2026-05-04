// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

// https://astro.build/config
export default defineConfig({
  site: 'https://orthodox-site.pages.dev',
  integrations: [sitemap(), mdx()],
  i18n: {
    defaultLocale: 'el',
    locales: ['el', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
