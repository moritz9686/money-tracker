import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../core/config/api_config.dart';
import '../core/networking/api_client.dart';
import '../data/repositories/api_transaction_repository.dart';
import '../data/repositories/api_gmail_repository.dart';
import '../data/repositories/api_reference_data_repository.dart';
import '../data/repositories/mock_repositories.dart';
import '../data/repositories/supabase_auth_repository.dart';
import '../domain/repositories/repositories.dart';
import 'screens/app_screens.dart';

class AppDependencies {
  const AppDependencies({
    required this.authRepository,
    required this.transactionRepository,
    required this.referenceDataRepository,
    required this.gmailRepository,
  });

  final AuthRepository authRepository;
  final TransactionRepository transactionRepository;
  final ReferenceDataRepository referenceDataRepository;
  final GmailRepository? gmailRepository;

  factory AppDependencies.production() {
    final auth = ApiConfig.useMockData
        ? MockAuthRepository()
        : SupabaseAuthRepository(Supabase.instance.client);
    final client = HttpApiClient(
      baseUrl: ApiConfig.baseUrl,
      headersProvider: () => {
        if (auth.accessToken != null) 'Authorization': 'Bearer ${auth.accessToken}',
      },
    );
    return AppDependencies(
        authRepository: auth,
        transactionRepository: ApiConfig.useMockData
            ? MockTransactionRepository()
            : ApiTransactionRepository(client),
        referenceDataRepository: ApiConfig.useMockData
            ? MockReferenceDataRepository()
            : ApiReferenceDataRepository(client),
        gmailRepository: ApiConfig.useMockData ? null : ApiGmailRepository(client),
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
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xff6750e8),
            primary: const Color(0xff6750e8),
            surface: const Color(0xfff8f7ff),
          ),
          useMaterial3: true,
          scaffoldBackgroundColor: const Color(0xfff8f7ff),
          cardTheme: CardThemeData(
            margin: EdgeInsets.zero,
            elevation: 0,
            color: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        home: SplashScreen(dependencies: dependencies),
      );
}
