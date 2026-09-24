import 'presentation/app.dart';
import 'package:flutter/widgets.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(MoneyTrackerApp(dependencies: AppDependencies.mock()));
}
