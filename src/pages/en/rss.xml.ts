import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const all = await getCollection('articles');
  const items = all
    .filter(a => a.data.language === 'en' && !a.data.draft)
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
    .slice(0, 50)
    .map(a => ({
      title: a.data.title,
      pubDate: a.data.pubDate,
      description: a.data.description,
      link: `/en/articles/${a.id}/`,
      author: a.data.author,
      categories: a.data.tags ?? [],
    }));

  return rss({
    title: 'Orthodox Logos',
    description: 'Patristic texts, lives of saints, liturgical services — with respect for the sources.',
    site: context.site!,
    items,
    customData: '<language>en</language>',
  });
}
