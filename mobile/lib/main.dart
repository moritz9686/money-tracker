import 'presentation/app.dart';
import 'package:flutter/widgets.dart';
import 'core/config/api_config.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!ApiConfig.useMockData) {
    if (ApiConfig.supabaseUrl.isEmpty || ApiConfig.supabasePublishableKey.isEmpty) {
      throw StateError('SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are required');
    }
    await Supabase.initialize(
      url: ApiConfig.supabaseUrl,
      anonKey: ApiConfig.supabasePublishableKey,
    );
  }
  runApp(MoneyTrackerApp(dependencies: AppDependencies.production()));
}
