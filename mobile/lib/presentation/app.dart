import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../core/config/api_config.dart';
import '../core/networking/api_client.dart';
import '../data/repositories/api_transaction_repository.dart';
import '../data/repositories/mock_repositories.dart';
import '../data/repositories/supabase_auth_repository.dart';
import '../domain/repositories/repositories.dart';
import 'screens/app_screens.dart';

class AppDependencies {
  const AppDependencies({
    required this.authRepository,
    required this.transactionRepository,
    required this.referenceDataRepository,
  });

  final AuthRepository authRepository;
  final TransactionRepository transactionRepository;
  final ReferenceDataRepository referenceDataRepository;

  factory AppDependencies.production() {
    final auth = ApiConfig.useMockData
        ? MockAuthRepository()
        : SupabaseAuthRepository(Supabase.instance.client);
    return AppDependencies(
        authRepository: auth,
        transactionRepository: ApiConfig.useMockData
            ? MockTransactionRepository()
            : ApiTransactionRepository(
                HttpApiClient(
                  baseUrl: ApiConfig.baseUrl,
                  headersProvider: () => {
                    if (auth.accessToken != null) 'Authorization': 'Bearer ${auth.accessToken}',
                  },
                ),
              ),
        referenceDataRepository: MockReferenceDataRepository(),
      );
  }
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
