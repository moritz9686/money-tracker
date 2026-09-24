import 'package:flutter/material.dart';

import '../data/repositories/mock_repositories.dart';
import '../domain/repositories/repositories.dart';
import 'screens/app_screens.dart';

class AppDependencies {
  const AppDependencies({
    required this.authRepository,
    required this.transactionRepository,
  });

  final AuthRepository authRepository;
  final TransactionRepository transactionRepository;

  factory AppDependencies.mock() => AppDependencies(
        authRepository: MockAuthRepository(),
        transactionRepository: MockTransactionRepository(),
      );
}

class MoneyTrackerApp extends StatelessWidget {
  const MoneyTrackerApp({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Money Tracker',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff146c94)),
          useMaterial3: true,
          cardTheme: const CardThemeData(margin: EdgeInsets.zero),
        ),
        home: SplashScreen(dependencies: dependencies),
      );
}
