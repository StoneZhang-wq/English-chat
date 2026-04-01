import 'package:flutter/foundation.dart';

@immutable
class P2pScenarioCard {
  final String id;
  final String title;
  final String categoryLabel;
  final String scenarioLabel;
  final String task;

  const P2pScenarioCard({
    required this.id,
    required this.title,
    required this.categoryLabel,
    required this.scenarioLabel,
    required this.task,
  });
}

@immutable
class P2pRoleSpec {
  final String partnerRole;
  final String yourRole;
  final String task;

  const P2pRoleSpec({
    required this.partnerRole,
    required this.yourRole,
    required this.task,
  });
}

