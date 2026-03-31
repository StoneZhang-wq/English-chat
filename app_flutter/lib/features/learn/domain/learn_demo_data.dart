import 'learn_models.dart';

const demoCategories = <LearnCategory>[
  LearnCategory(
    id: 'daily_life',
    title: 'Daily Life',
    subtitle: 'Explore',
  ),
  LearnCategory(
    id: 'workplace',
    title: 'Workplace',
    subtitle: 'Explore',
  ),
  LearnCategory(
    id: 'travel',
    title: 'Travel',
    subtitle: 'Explore',
  ),
];

const demoScenarios = <LearnScenario>[
  LearnScenario(
    id: 'coffee_shop',
    categoryId: 'daily_life',
    title: 'Coffee Shop',
    subtitle: 'View characters',
  ),
  LearnScenario(
    id: 'grocery_store',
    categoryId: 'daily_life',
    title: 'Grocery Store',
    subtitle: 'View characters',
  ),
  LearnScenario(
    id: 'job_interview',
    categoryId: 'workplace',
    title: 'Job Interview',
    subtitle: 'View characters',
  ),
];

const demoNpcs = <LearnNpc>[
  LearnNpc(
    id: 'barista_ben',
    scenarioId: 'coffee_shop',
    name: 'Barista Ben',
    description: 'Friendly barista. Speaks quickly but clearly.',
    initials: 'B',
  ),
  LearnNpc(
    id: 'manager_sarah',
    scenarioId: 'coffee_shop',
    name: 'Manager Sarah',
    description: 'Professional manager. Calm and helpful.',
    initials: 'S',
  ),
  LearnNpc(
    id: 'hr_heather',
    scenarioId: 'job_interview',
    name: 'HR Heather',
    description: 'HR interviewer. Focuses on behavior questions.',
    initials: 'H',
  ),
];

const demoTopics = <LearnTopic>[
  LearnTopic(
    id: 'order_special_drink',
    npcId: 'barista_ben',
    title: 'Ordering a specialized drink',
    subtitle: 'Order a drink and handle small talk with the barista.',
  ),
  LearnTopic(
    id: 'complain_wrong_order',
    npcId: 'manager_sarah',
    title: 'Complain about the wrong order',
    subtitle: 'Ask for a remake politely but firmly.',
  ),
  LearnTopic(
    id: 'behavior_interview_q1',
    npcId: 'hr_heather',
    title: 'Answer a behavior interview question',
    subtitle: 'Use STAR method to structure your answer.',
  ),
];

