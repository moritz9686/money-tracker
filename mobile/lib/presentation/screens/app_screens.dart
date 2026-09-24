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
      AccountsScreen(repository: widget.dependencies.referenceDataRepository),
      CategoriesScreen(repository: widget.dependencies.referenceDataRepository),
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
  Widget build(BuildContext context) => FutureBuilder<TransactionPage>(
        future: repository.getTransactions(const TransactionQuery()),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return EmptyState(message: 'Could not load dashboard. ${snapshot.error}');
          }
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final transactions = snapshot.data!.items;
          if (transactions.isEmpty) return const EmptyState(message: 'No transactions yet.');
          final income = transactions
              .where((item) => item.type == TransactionType.credit)
              .fold(0, (sum, item) => sum + item.amount.minorUnits);
          final expenses = transactions
              .where((item) => item.type == TransactionType.debit)
              .fold(0, (sum, item) => sum + item.amount.minorUnits);
          final byCategory = <String, int>{};
          final byMode = <String, int>{};
          for (final item in transactions.where((item) => item.type == TransactionType.debit)) {
            byCategory.update(item.category?.name ?? 'Uncategorized', (amount) => amount + item.amount.minorUnits,
                ifAbsent: () => item.amount.minorUnits);
            byMode.update(_paymentModeLabel(item.paymentMode), (amount) => amount + item.amount.minorUnits,
                ifAbsent: () => item.amount.minorUnits);
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
                  SummaryCard(label: 'Income', amount: Money.fromMinorUnits(income, 'INR'), color: Colors.green),
                  SummaryCard(label: 'Expenses', amount: Money.fromMinorUnits(expenses, 'INR'), color: Colors.red),
                  SummaryCard(label: 'Net balance', amount: Money.fromMinorUnits(income - expenses, 'INR'), color: Colors.blue),
                ],
              ),
              const SizedBox(height: 24),
              Text('Recent transactions', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...transactions.take(3).map(
                    (transaction) => TransactionListTile(
                      transaction: transaction,
                      repository: repository,
                    ),
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

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({required this.repository, super.key});

  final TransactionRepository repository;

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  static const _pageSize = 20;
  final _merchantController = TextEditingController();
  TransactionType? _transactionType;
  PaymentMode? _paymentMode;
  final _items = <FinancialTransaction>[];
  var _total = 0;
  var _loading = true;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _load(reset: true);
  }

  @override
  void dispose() {
    _merchantController.dispose();
    super.dispose();
  }

  Future<void> _load({required bool reset}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await widget.repository.getTransactions(
        TransactionQuery(
          limit: _pageSize,
          offset: reset ? 0 : _items.length,
          transactionType: _transactionType,
          paymentMode: _paymentMode,
          merchant: _merchantController.text.trim(),
        ),
      );
      if (!mounted) return;
      setState(() {
        _items
          ..clear()
          ..addAll(reset ? page.items : [..._items, ...page.items]);
        _total = page.total;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _items.isEmpty) return const Center(child: CircularProgressIndicator());
    if (_error != null && _items.isEmpty) {
      return _RetryState(message: 'Could not load transactions.', onRetry: () => _load(reset: true));
    }
    return RefreshIndicator(
      onRefresh: () => _load(reset: true),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _merchantController,
            decoration: InputDecoration(
              labelText: 'Search merchant',
              suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: () => _load(reset: true)),
            ),
            onSubmitted: (_) => _load(reset: true),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              ChoiceChip(label: const Text('All'), selected: _transactionType == null, onSelected: (_) { setState(() => _transactionType = null); _load(reset: true); }),
              ChoiceChip(label: const Text('Debits'), selected: _transactionType == TransactionType.debit, onSelected: (_) { setState(() => _transactionType = TransactionType.debit); _load(reset: true); }),
              ChoiceChip(label: const Text('Credits'), selected: _transactionType == TransactionType.credit, onSelected: (_) { setState(() => _transactionType = TransactionType.credit); _load(reset: true); }),
              ChoiceChip(label: const Text('UPI'), selected: _paymentMode == PaymentMode.upi, onSelected: (_) { setState(() => _paymentMode = _paymentMode == PaymentMode.upi ? null : PaymentMode.upi); _load(reset: true); }),
              ChoiceChip(label: const Text('Card'), selected: _paymentMode == PaymentMode.card, onSelected: (_) { setState(() => _paymentMode = _paymentMode == PaymentMode.card ? null : PaymentMode.card); _load(reset: true); }),
            ],
          ),
          const SizedBox(height: 12),
          if (_items.isEmpty) const EmptyState(message: 'No transactions match these filters.'),
          ..._items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: TransactionListTile(
                  transaction: item,
                  repository: widget.repository,
                ),
              )),
          if (_items.length < _total)
            OutlinedButton(
              onPressed: _loading ? null : () => _load(reset: false),
              child: Text(_loading ? 'Loading…' : 'Load more'),
            ),
          if (_error != null && _items.isNotEmpty)
            TextButton(onPressed: () => _load(reset: false), child: const Text('Retry loading more')),
        ],
      ),
    );
  }
}

class TransactionListTile extends StatelessWidget {
  const TransactionListTile({
    required this.transaction,
    required this.repository,
    super.key,
  });

  final FinancialTransaction transaction;
  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: CircleAvatar(child: Text(transaction.category?.icon ?? '₹')),
          title: Text(transaction.merchant ?? 'Unknown merchant'),
          subtitle: Text('${transaction.category?.name ?? 'Uncategorized'} • ${_dateLabel(transaction.date)}'),
          trailing: Text(
            '${transaction.type == TransactionType.debit ? '-' : '+'}${formatMoney(transaction.amount)}',
            style: TextStyle(
              color: transaction.type == TransactionType.debit ? Colors.red : Colors.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => TransactionDetailsScreen(
                transactionId: transaction.id,
                repository: repository,
              ),
            ),
          ),
        ),
      );
}

class TransactionDetailsScreen extends StatelessWidget {
  const TransactionDetailsScreen({
    required this.transactionId,
    required this.repository,
    super.key,
  });

  final String transactionId;
  final TransactionRepository repository;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Transaction details')),
        body: FutureBuilder<FinancialTransaction>(
          future: repository.getTransaction(transactionId),
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return _RetryState(
                message: 'Could not load transaction details.',
                onRetry: () => Navigator.of(context).pushReplacement(
                  MaterialPageRoute(
                    builder: (_) => TransactionDetailsScreen(
                      transactionId: transactionId,
                      repository: repository,
                    ),
                  ),
                ),
              );
            }
            if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
            return _TransactionDetailsBody(transaction: snapshot.data!);
          },
        ),
      );
}

class _TransactionDetailsBody extends StatelessWidget {
  const _TransactionDetailsBody({required this.transaction});
  final FinancialTransaction transaction;

  @override
  Widget build(BuildContext context) => ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Icon(Icons.receipt_long_outlined, size: 64, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 12),
            Text(transaction.merchant ?? 'Unknown merchant', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(formatMoney(transaction.amount), textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 28),
            _DetailRow(label: 'Type', value: transaction.type.name.toUpperCase()),
            _DetailRow(label: 'Category', value: transaction.category?.name ?? 'Uncategorized'),
            _DetailRow(label: 'Payment mode', value: _paymentModeLabel(transaction.paymentMode)),
            _DetailRow(label: 'Account', value: transaction.accountName ?? transaction.accountLast4 ?? 'Not available'),
            _DetailRow(label: 'Bank', value: transaction.bankName ?? 'Not available'),
            _DetailRow(label: 'Reference', value: transaction.referenceId ?? 'Not available'),
            _DetailRow(label: 'Date', value: _dateLabel(transaction.date)),
            _DetailRow(label: 'Description', value: transaction.description ?? 'Not available'),
          ],
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

class _RetryState extends StatelessWidget {
  const _RetryState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(onPressed: onRetry, child: const Text('Retry')),
            ],
          ),
        ),
      );
}

class AccountsScreen extends StatelessWidget {
  const AccountsScreen({required this.repository, super.key});
  final ReferenceDataRepository repository;

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
                  trailing: Text(formatMoney(account.balance)),
                ),
              );
            },
          );
        },
      );
}

class CategoriesScreen extends StatelessWidget {
  const CategoriesScreen({required this.repository, super.key});
  final ReferenceDataRepository repository;

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
