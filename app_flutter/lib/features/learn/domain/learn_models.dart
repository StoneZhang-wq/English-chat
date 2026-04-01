import 'package:flutter/foundation.dart';

@immutable
class LearnCategory {
  final String id;
  final String title;
  final String subtitle;

  const LearnCategory({
    required this.id,
    required this.title,
    required this.subtitle,
  });
}

@immutable
class LearnScenario {
  final String id;
  final String categoryId;
  final String title;
  final String subtitle;

  const LearnScenario({
    required this.id,
    required this.categoryId,
    required this.title,
    required this.subtitle,
  });
}

@immutable
class LearnNpc {
  final String id;
  final String scenarioId;
  final String name;
  final String description;
  final String initials;

  const LearnNpc({
    required this.id,
    required this.scenarioId,
    required this.name,
    required this.description,
    required this.initials,
  });
}

@immutable
class LearnTopic {
  final String id;
  final String npcId;
  final String title;
  final String subtitle;

  const LearnTopic({
    required this.id,
    required this.npcId,
    required this.title,
    required this.subtitle,
  });
}

