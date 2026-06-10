import { useTranslation } from 'react-i18next';

type TextMap = Record<string, string>;

const ruStages: TextMap = {
  Access: 'Доступ',
  Mapping: 'Картирование',
  Qualifying: 'Квалификация',
};

const ruOwners: TextMap = {
  'Account Executive': 'Менеджер аккаунта',
  'Partner Manager': 'Партнерский менеджер',
  RevOps: 'RevOps',
  SDR: 'SDR',
};

const ruRouteTypes: TextMap = {
  dark_stakeholder_discovery: 'поиск скрытых стейкхолдеров',
  partner_intro: 'партнерское интро',
  procurement_discovery: 'прояснение закупочного пути',
  technical_benchmark: 'технический бенчмарк',
};

const ruRouteTitles: TextMap = {
  dark_stakeholder_discovery: 'Исследовать недостающих стейкхолдеров до прямого хода',
  partner_intro: 'Запросить партнерское интро',
  procurement_discovery: 'Картировать закупочный путь до аутрича',
  technical_benchmark: 'Пригласить технического стейкхолдера на бенчмарк',
};

const ruSignalKinds: TextMap = {
  hiring: 'найм',
  procurement: 'закупка',
};

const ruRoles: TextMap = {
  'Head of Data': 'Руководитель данных',
  'Head of Data Platform': 'Руководитель платформы данных',
  Integrator: 'Интегратор',
  'Procurement Lead': 'Руководитель закупок',
  CIO: 'CIO',
  'Operations Sponsor': 'Операционный спонсор',
  'Security Architect': 'Архитектор безопасности',
  'VP Engineering': 'VP Engineering',
  economic_buyer: 'экономический покупатель',
  procurement_role: 'роль закупок',
  security_gatekeeper: 'гейткипер безопасности',
  technical_champion: 'технический чемпион',
};

const ruStates: TextMap = {
  selected: 'выбран',
  identified: 'выявлен',
  hypothesis: 'гипотеза',
  blocker: 'блокер',
  missing: 'не выявлен',
};

const ruPlaybookTokens: TextMap = {
  all: 'все маршруты',
  cold_telegram: 'холодный Telegram',
  partner_case_data_platform: 'партнерский кейс по платформе данных',
  partner_case_healthcare: 'партнерский кейс по healthcare',
  partner_case_logistics: 'партнерский кейс по логистике',
  partner_case_manufacturing: 'партнерский кейс по производству',
  partner_case_platform: 'партнерский кейс по платформе',
  data_benchmark_report: 'отчет data benchmark',
};

const ruTexts: TextMap = {
  'Automation platform team added six engineering roles after a public efficiency initiative.':
    'Команда автоматизационной платформы открыла шесть инженерных ролей после публичной инициативы по эффективности.',
  'Automation platform team added six engineering roles after a public efficiency initiative.; София Чернова can become a technical champion.':
    'Команда автоматизационной платформы открыла шесть инженерных ролей после публичной инициативы по эффективности; София Чернова может стать техническим чемпионом.',
  'BI consulting purchase was recorded eight months ago, creating a procurement trail.':
    'Закупка BI-консалтинга зафиксирована восемь месяцев назад и создает закупочный след.',
  'Data operations team opened analytics engineering roles tied to route optimization.':
    'Команда data operations открыла роли analytics engineering, связанные с оптимизацией маршрутов.',
  'Digital health analytics RFI asks vendors to describe governed data access.':
    'RFI по аналитике digital health просит вендоров описать управляемый доступ к данным.',
  'Low-confidence procurement notice references a future reporting platform review.':
    'Низкодостоверное закупочное уведомление упоминает будущий пересмотр отчетной платформы.',
  'Manufacturing analytics services purchase indicates an active buying process.':
    'Закупка сервисов производственной аналитики указывает на активный процесс покупки.',
  'Recent SI partner tender references platform modernization.':
    'Свежий тендер SI-партнера упоминает модернизацию платформы.',
  'Seven open Data Engineer and DWH Architect roles suggest an active data platform initiative.':
    'Семь открытых ролей Data Engineer и DWH Architect указывают на активную инициативу по платформе данных.',
  'Data operations team opened analytics engineering roles tied to route optimization.; Майя Коган can become a technical champion.':
    'Команда data operations открыла роли analytics engineering, связанные с оптимизацией маршрутов; Майя Коган может стать техническим чемпионом.',
  'Seven open Data Engineer and DWH Architect roles suggest an active data platform initiative.; Иван Петров can become a technical champion.':
    'Семь открытых ролей Data Engineer и DWH Architect указывают на активную инициативу по платформе данных; Иван Петров может стать техническим чемпионом.',
  'Геликс Системы is connected to the account as partner.': 'Геликс Системы связан с аккаунтом как партнер.',
  'Икс-Софт is connected to the account as partner.': 'Икс-Софт связан с аккаунтом как партнер.',
  'Маршрутные Системы is connected to the account as partner.': 'Маршрутные Системы связаны с аккаунтом как партнер.',
  'МедСис Консалтинг is connected to the account as partner.': 'МедСис Консалтинг связан с аккаунтом как партнер.',
  'ФабрикаСофт is connected to the account as partner.': 'ФабрикаСофт связан с аккаунтом как партнер.',
  'Missing roles must be surfaced before outreach: economic_buyer, technical_champion, security_gatekeeper.':
    'Перед аутричем нужно выявить недостающие роли: экономический покупатель, технический чемпион, гейткипер безопасности.',
  'Missing roles must be surfaced before outreach: economic_buyer.':
    'Перед аутричем нужно выявить экономического покупателя.',
  'Missing roles must be surfaced before outreach: security_gatekeeper.':
    'Перед аутричем нужно выявить гейткипера безопасности.',
  'Careers page lists automation platform engineering vacancies.':
    'Страница вакансий показывает инженерные роли по автоматизационной платформе.',
  'Hiring page lists Data Engineer and DWH Architect vacancies.':
    'Страница найма показывает вакансии Data Engineer и DWH Architect.',
  'Hiring page lists analytics engineering roles.': 'Страница найма показывает роли analytics engineering.',
  'Procurement notice references reporting platform review.':
    'Закупочное уведомление упоминает пересмотр отчетной платформы.',
  'Procurement record mentions BI consulting services.':
    'Закупочная запись упоминает услуги BI-консалтинга.',
  'Procurement record mentions manufacturing analytics services.':
    'Закупочная запись упоминает сервисы производственной аналитики.',
  'RFI includes governed analytics access requirements.':
    'RFI включает требования к управляемому доступу к аналитике.',
  'Tender record mentions platform modernization services.':
    'Тендерная запись упоминает услуги модернизации платформы.',
  'Economic buyer is not confirmed yet.': 'Экономический покупатель еще не подтвержден.',
  'Formal route can be slow and may expose the team too late.':
    'Формальный маршрут может быть медленным и слишком поздно показать команду.',
  'Partner may be aligned with an incumbent competitor.':
    'Партнер может быть на стороне инкамбент-конкурента.',
  'Premature outreach can look irrelevant.': 'Преждевременный аутрич может выглядеть нерелевантным.',
  'Allowed by playbook and supported by account evidence.':
    'Разрешено плейбуком и подтверждено доказательствами по аккаунту.',
  'Partner motion disabled in this what-if playbook.':
    'Партнерский ход отключен в этом what-if варианте плейбука.',
  'Route is not allowed by this playbook.': 'Этот маршрут не разрешен выбранным плейбуком.',
  'No surfaced partner role is connected to this account.':
    'В аккаунте нет выявленной партнерской роли для этого маршрута.',
  'Needs both a technical stakeholder and a hiring signal.':
    'Нужны одновременно технический стейкхолдер и сигнал найма.',
  'Needs a procurement signal before this route can be ranked.':
    'Перед ранжированием нужен закупочный сигнал.',
  'Missing roles exist, but stronger allowed routes outrank this discovery move.':
    'Недостающие роли есть, но более сильные разрешенные маршруты выше в preview.',
  'No missing roles are present in the current account artifact.':
    'В текущем артефакте аккаунта нет недостающих ролей.',
  'Route conditions are not met.': 'Условия маршрута не выполнены.',
  'Head of Data: identified -> engaged / champion_candidate':
    'Руководитель данных: выявлен -> вовлечен / кандидат в чемпионы',
  'Head of Data Platform: identified -> engaged / champion_candidate':
    'Руководитель платформы данных: выявлен -> вовлечен / кандидат в чемпионы',
  'missing_roles: unknown -> research_queue':
    'недостающие роли: неизвестно -> очередь на исследование',
  'partner_route: hypothesis -> verified': 'партнерский маршрут: гипотеза -> подтвержден',
  'procurement_role: unknown -> identified': 'роль закупок: неизвестно -> выявлена',
};

function localize(value: string | null | undefined, map: TextMap, enabled: boolean) {
  if (!value || !enabled) {
    return value ?? '';
  }
  return map[value] ?? value;
}

function humanize(value: string) {
  return value.replaceAll('_', ' ');
}

function localizeToken(value: string, map: TextMap, enabled: boolean) {
  if (!enabled) {
    return humanize(value);
  }
  return map[value] ?? humanize(value);
}

export function useDemoLocalization() {
  const { i18n } = useTranslation();
  const ru = i18n.language.startsWith('ru');

  return {
    owner: (value: string | null | undefined) => localize(value, ruOwners, ru),
    playbookToken: (value: string) => localizeToken(value, ruPlaybookTokens, ru),
    role: (value: string) => localize(value, ruRoles, ru),
    routeTitle: (routeType: string, fallback: string) => (ru ? ruRouteTitles[routeType] ?? fallback : fallback),
    routeType: (value: string) => (ru ? ruRouteTypes[value] ?? humanize(value) : humanize(value)),
    signalKind: (value: string) => localize(value, ruSignalKinds, ru),
    stage: (value: string) => localize(value, ruStages, ru),
    state: (value: string) => localize(value, ruStates, ru),
    text: (value: string) => localize(value, ruTexts, ru),
  };
}
