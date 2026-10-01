# Marketing Agent Kit

Скиллы, агент-критик и инструкции по подключениям для маркетинговой работы в [Claude Code](https://code.claude.com): исследование конкурентов, разбор рекламы из библиотек, скриншоты чужих воронок, SEO-данные, отчёты GA4, генерация картинок, моушн-карточки из кода, библиотека рекламных роликов со страницей ревью и тексты, которые незнакомый человек понимает с первого прочтения.

Собрано из реальной работы growth-команды B2B SaaS в 2026 году и очищено от всего, что относится к конкретной компании. [English →](README.md)

## Что внутри

### Скиллы

| Скилл | Что делает | Что нужно |
|---|---|---|
| [`competitor-research`](skills/competitor-research/SKILL.md) | Полное досье на конкурента по домену: сайт, клиенты, цены, комьюнити, реклама, SEO, команда, PR. ~17 субагентов и deep research, на выходе база знаний и HTML-отчёт | Parallel, SearchApi, Ahrefs |
| [`parallel-research`](skills/parallel-research/SKILL.md) | Глубокий веб-рисерч со ссылками (от минут до часа) и быстрый поиск с источниками, плюс гайд по написанию брифов | Parallel |
| [`ads-parser`](skills/ads-parser/SKILL.md) | Реклама компании из библиотек LinkedIn, Google и Meta: точные тексты, даты, раскрытые показы, ссылки | SearchApi |
| [`ahrefs-seo`](skills/ahrefs-seo/SKILL.md) | Органические ключи, топ-страницы, бэклинки, DR, частотности. С моделью стоимости юнитов, чтобы выгрузки не съели тариф | Ahrefs (платный) |
| [`ga4-reports`](skills/ga4-reports/SKILL.md) | Отчёты GA4, сравнение периодов и воронки, ловушки отчётности и запасной путь через REST, если MCP завис | вход в Google |
| [`image-gen`](skills/image-gen/SKILL.md) | Генерация и редактирование картинок через OpenAI GPT Image. Качество под задачу, правила арт-дирекшна | ключ OpenAI |
| [`funnel-screenshots`](skills/funnel-screenshots/SKILL.md) | Проходит публичный квиз или онбординг в эмуляции iPhone и снимает каждый экран retina-скриншотом, плюс пейволл и модалки со скидками. Платёжные данные не вводит никогда | Python, Playwright (ставится сам) |
| [`motion-card`](skills/motion-card/SKILL.md) | Финальные карточки, заставки, анимированные CTA и логотипы из HTML/CSS/GSAP через HyperFrames, с озвучкой ElevenLabs. Сначала звук, потом картинка; озвучка сверяется со сценарием | Node 22+, FFmpeg, ElevenLabs |
| [`ads-video-library`](skills/ads-video-library/SKILL.md) | Канонические имена, постер (вшивается в кадр 0), контакт-листы, хранение Месяц / Язык / Тип (локально или в Google Drive), CSV-каталог и страница ревью `gallery.html` | FFmpeg |
| [`plain-copy`](skills/plain-copy/SKILL.md) | Правила для текстов, которые понятны незнакомцу и не звучат как написанные машиной, с примерами «было / стало» | — |
| [`connect`](skills/connect/SKILL.md) | Пошагово настраивает ключи, вход в Google и MCP-серверы; `doctor` проверяет каждый ключ бесплатным запросом | — |

### Агент

| Агент | Что делает |
|---|---|
| [`copy-critic`](agents/copy-critic.md) | Читает рекламный текст глазами человека, который листает ленту, и по каждой строке выносит вердикт с готовой переписанной версией. [Как обучить такого критика на своих правках →](docs/train-your-critic.md) |

### Подключения

На каждый сервис отдельная инструкция: доступ, стоимость, установка, проверка, безопасность, грабли. Все в [connections/](connections/README.md).

Google Ads · GA4 · Ahrefs · Stripe · BigQuery · Playwright · Parallel · SearchApi · ElevenLabs · OpenAI Images · HyperFrames · Higgsfield

## Прочитайте до установки

**Не ставьте скиллы бездумно, в том числе эти.** Каждый установленный скилл добавляет своё описание в каждый разговор и конкурирует за внимание Claude. А скилл, написанный под чужой процесс, тихо делает всё по-чужому. Относитесь к ним как к шаблонам:

1. Прочитайте `SKILL.md` тех, что нужны. Они короткие.
2. Ставьте только то, чем будете пользоваться в этом месяце.
3. В конце каждого скилла есть раздел **«Adapt it»**. Сделайте то, что там написано. Скиллы становятся хорошими, когда в них лежат *ваши* правки: ваши правила отчётов, ваши события воронки, ваши паттерны текстов, ваш бренд.

## Установка

**Как плагин** (терминал Claude Code или десктоп-приложение):

```
/plugin marketplace add tymoshenko-dmytro/marketing-agent-kit
/plugin install marketing-agent-kit@marketing-agent-kit
```

Скиллы появятся как `/marketing-agent-kit:<skill>`. Claude подхватывает их и сам, по смыслу запроса.

**Или скопируйте нужное:**

```bash
git clone https://github.com/tymoshenko-dmytro/marketing-agent-kit.git
cp -R marketing-agent-kit/skills/ads-parser ~/.claude/skills/        # один скилл, во всех проектах
cp marketing-agent-kit/agents/copy-critic.md ~/.claude/agents/       # критик
```

Чтобы скилл работал только в одном проекте, кладите его в `<проект>/.claude/skills/` вместо `~/.claude/skills/`.

## Первый запуск

Напишите Claude: **«Настрой кит для исследования конкурентов»** (или что вам нужно). Скилл `connect` создаст приватный файл для ключей, проведёт по получению каждого ключа, зарегистрирует MCP-серверы и проверит, что всё работает:

```bash
python3 skills/connect/scripts/kit.py init           # ~/.config/marketing-agent-kit/.env, chmod 600
python3 skills/connect/scripts/kit.py doctor --live  # что работает, чего не хватает
```

## Ключи и приватность

- Все ключи лежат в **одном файле вне любого репозитория**: `~/.config/marketing-agent-kit/.env` (шаблон: [.env.example](.env.example)). Вписываете их туда вы сами.
- **Не вставляйте ключи в чат.** Чаты сохраняются на диск. Скрипты читают ключи из файла и никогда их не печатают.
- Где сервис позволяет, выбирайте OAuth, права только на чтение и лимиты расходов. В каждой инструкции написано, как это сделать.
- Результаты исследований (`raw/`, `dist/`, каталоги) внесены в `.gitignore`. Не тащите данные клиентов в свои форки.

## Требования

- Python 3.9+. Скрипты используют только стандартную библиотеку; для режима Google Drive в `ads-video-library` нужен `pip install google-auth requests`.
- FFmpeg для `ads-video-library` и `motion-card`. Node.js 18+ для Playwright MCP, 22+ для HyperFrames. `gcloud` и `pipx` для сервисов Google. ~400 МБ для `funnel-screenshots` (установка сама ставит Playwright и Chromium).

## Что ещё я использую (не входит в кит)

Хорошие работы других авторов. Перед установкой действует то же правило: сначала прочитать.

| Что | Зачем |
|---|---|
| [Marketing Skills](https://github.com/coreyhaines31/marketingskills), Corey Haines (MIT) | `product-marketing` создаёт файл с контекстом продукта, который читают другие скиллы и `copy-critic`. Плюс CRO, копирайтинг, SEO-аудит, письма, A/B-тесты |
| Скиллы Anthropic для документов (`docx`, `pdf`, `pptx`, `xlsx`) | презентации, отчёты и таблицы файлами, доступны в приложениях Claude |
| [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) | видео, собранные из HTML/CSS; хорошо работает в паре с `ads-video-library` |
| [Скиллы Higgsfield](https://github.com/higgsfield-ai/skills) (MIT) | генеративная видео- и фото-реклама |
| [/brag](https://github.com/latent-spaces/brag) (MIT) | промо-ролики того, что вы сделали; отсюда идея постера и кадра 0 |
| [Impeccable](https://github.com/pbakaus/impeccable) | команды дизайн-ревью (audit, polish, critique) для лендингов |
| [Humanizer](https://github.com/blader/humanizer) (MIT) | вычищает приметы AI-текста из длинных материалов |

## Благодарности

- Выбор постера и вшивание его в кадр 0 в `ads-video-library` взяты из [/brag](https://github.com/latent-spaces/brag) (автор Shunit Haviv Hakimi, MIT).
- Факты по подключениям сверены с документацией сервисов 1 октября 2026.

## Лицензия

[MIT](LICENSE) © 2026 Dmytro Tymoshenko · [LinkedIn](https://www.linkedin.com/in/tymoshenko-dmytro)
