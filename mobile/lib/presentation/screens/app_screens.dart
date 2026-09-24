import 'package:flutter/material.dart';

import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';
import '../app.dart';
import '../widgets/finance_widgets.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _continue();
  }

  Future<void> _continue() async {
    final signedIn = await widget.dependencies.authRepository.isSignedIn();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => signedIn
            ? AppShell(dependencies: widget.dependencies)
            : LoginScreen(dependencies: widget.dependencies),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.account_balance_wallet_outlined, size: 64),
              SizedBox(height: 16),
              Text('Money Tracker'),
              SizedBox(height: 20),
              CircularProgressIndicator(),
            ],
          ),
        ),
      );
}

class LoginScreen extends StatelessWidget {
  const LoginScreen({required this.dependencies, super.key});

  final AppDependencies dependencies;

  Future<void> _signIn(BuildContext context) async {
    await dependencies.authRepository.signInForDevelopment();
    if (!context.mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => AppShell(dependencies: dependencies)),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Spacer(),
                Icon(
                  Icons.account_balance_wallet_outlined,
                  size: 84,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(height: 24),
                Text(
                  'Your money, clearly organized.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 12),
                const Text(
                  'Authentication will be connected to the backend in a later milestone. This build uses safe mock data.',
                  textAlign: TextAlign.center,
                ),
                const Spacer(),
                FilledButton.icon(
                  onPressed: () => _signIn(context),
                  icon: const Icon(Icons.login),
                  label: const Text('Continue with demo data'),
                ),
              ],
            ),
          ),
        ),
      );
}

class AppShell extends StatefulWidget {
  const AppShell({required this.dependencies, super.key});

  final AppDependencies dependencies;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  var _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardScreen(repository: widget.dependencies.transactionRepository),
      TransactionsScreen(repository: widget.dependencies.transactionRepository),
      AccountsScreen(repository: widget.dependencies.transactionRepository),
      CategoriesScreen(repository: widget.dependencies.transactionRepository),
      SettingsScreen(dependencies: widget.dependencies),
    ];
    const titles = ['Dashboard', 'Transactions', 'Accounts', 'Categories', 'Settings'];
    return Scaffold(
      appBar: AppBar(title: Text(titles[_selectedIndex])),
      body: pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Activity'),
          NavigationDestination(icon: Icon(Icons.account_balance_outlined), label: 'Accounts'),
          NavigationDestination(icon: Icon(Icons.category_outlined), label: 'Categories'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), label: 'Settings'),
        ],
      ),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({required this.repository, super.key});

  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<FinancialTransaction>>(
        future: repository.getTransactions(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final transactions = snapshot.data!;
          final income = transactions
              .where((item) => item.type == TransactionType.credit)
              .fold(0, (sum, item) => sum + item.amount);
          final expenses = transactions
              .where((item) => item.type == TransactionType.debit)
              .fold(0, (sum, item) => sum + item.amount);
          final byCategory = <String, int>{};
          final byMode = <String, int>{};
          for (final item in transactions.where((item) => item.type == TransactionType.debit)) {
            byCategory.update(item.category.name, (amount) => amount + item.amount,
                ifAbsent: () => item.amount);
            byMode.update(_paymentModeLabel(item.paymentMode), (amount) => amount + item.amount,
                ifAbsent: () => item.amount);
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('This month', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 2,
                childAspectRatio: 1.65,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 10,
                crossAxisSpacing: 10,
                children: [
                  SummaryCard(label: 'Income', amount: income, color: Colors.green),
                  SummaryCard(label: 'Expenses', amount: expenses, color: Colors.red),
                  SummaryCard(label: 'Net balance', amount: income - expenses, color: Colors.blue),
                ],
              ),
              const SizedBox(height: 24),
              Text('Recent transactions', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...transactions.take(3).map(
                    (transaction) => TransactionListTile(transaction: transaction),
                  ),
              const SizedBox(height: 20),
              Text('Spending by category', style: Theme.of(context).textTheme.titleMedium),
              ...byCategory.entries.map(
                (entry) => BreakdownRow(label: entry.key, amount: entry.value, total: expenses),
              ),
              const SizedBox(height: 20),
              Text('Spending by payment mode', style: Theme.of(context).textTheme.titleMedium),
              ...byMode.entries.map(
                (entry) => BreakdownRow(label: entry.key, amount: entry.value, total: expenses),
              ),
            ],
          );
        },
      );
}

class TransactionsScreen extends StatelessWidget {
  const TransactionsScreen({required this.repository, super.key});

  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<FinancialTransaction>>(
        future: repository.getTransactions(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final transactions = snapshot.data!;
          if (transactions.isEmpty) return const EmptyState(message: 'No transactions yet.');
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: transactions.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, index) => TransactionListTile(transaction: transactions[index]),
          );
        },
      );
}

class TransactionListTile extends StatelessWidget {
  const TransactionListTile({required this.transaction, super.key});

  final FinancialTransaction transaction;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: CircleAvatar(child: Text(transaction.category.icon)),
          title: Text(transaction.merchant),
          subtitle: Text('${transaction.category.name} • ${_dateLabel(transaction.date)}'),
          trailing: Text(
            '${transaction.type == TransactionType.debit ? '-' : '+'}${formatInr(transaction.amount)}',
            style: TextStyle(
              color: transaction.type == TransactionType.debit ? Colors.red : Colors.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => TransactionDetailsScreen(transaction: transaction),
            ),
          ),
        ),
      );
}

class TransactionDetailsScreen extends StatelessWidget {
  const TransactionDetailsScreen({required this.transaction, super.key});

  final FinancialTransaction transaction;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Transaction details')),
        body: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Icon(Icons.receipt_long_outlined, size: 64, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 12),
            Text(transaction.merchant, textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(formatInr(transaction.amount), textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 28),
            _DetailRow(label: 'Type', value: transaction.type.name.toUpperCase()),
            _DetailRow(label: 'Category', value: transaction.category.name),
            _DetailRow(label: 'Payment mode', value: _paymentModeLabel(transaction.paymentMode)),
            _DetailRow(label: 'Account', value: transaction.accountName),
            _DetailRow(label: 'Date', value: _dateLabel(transaction.date)),
            _DetailRow(label: 'Description', value: transaction.description),
          ],
        ),
      );
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium)),
            Flexible(child: Text(value, textAlign: TextAlign.end)),
          ],
        ),
      );
}

class AccountsScreen extends StatelessWidget {
  const AccountsScreen({required this.repository, super.key});
  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<FinancialAccount>>(
        future: repository.getAccounts(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: snapshot.data!.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (_, index) {
              final account = snapshot.data![index];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.account_balance_outlined),
                  title: Text(account.name),
                  subtitle: Text('•••• ${account.last4}'),
                  trailing: Text(formatInr(account.balance)),
                ),
              );
            },
          );
        },
      );
}

class CategoriesScreen extends StatelessWidget {
  const CategoriesScreen({required this.repository, super.key});
  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Category>>(
        future: repository.getCategories(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: snapshot.data!.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, index) {
              final category = snapshot.data![index];
              return Card(
                child: ListTile(
                  leading: Text(category.icon, style: const TextStyle(fontSize: 26)),
                  title: Text(category.name),
                ),
              );
            },
          );
        },
      );
}

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({required this.dependencies, super.key});
  final AppDependencies dependencies;

  Future<void> _signOut(BuildContext context) async {
    await dependencies.authRepository.signOut();
    if (!context.mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => LoginScreen(dependencies: dependencies)),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const ListTile(
            leading: Icon(Icons.info_outline),
            title: Text('Demo mode'),
            subtitle: Text('All information displayed is mock data.'),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sign out'),
            onTap: () => _signOut(context),
          ),
        ],
      );
}

String _paymentModeLabel(PaymentMode mode) => switch (mode) {
      PaymentMode.upi => 'UPI',
      PaymentMode.card => 'Card',
      PaymentMode.neft => 'NEFT',
      PaymentMode.imps => 'IMPS',
      PaymentMode.rtgs => 'RTGS',
      PaymentMode.atm => 'ATM',
      PaymentMode.cash => 'Cash',
      PaymentMode.other => 'Other',
    };

String _dateLabel(DateTime value) => '${value.day}/${value.month}/${value.year}';
