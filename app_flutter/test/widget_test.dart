import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:my_english_chat/app/app.dart';

void main() {
  testWidgets('Home shell shows app title', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MyEnglishChatApp(),
      ),
    );

    expect(find.text('MyEnglishChat'), findsOneWidget);
  });
}
