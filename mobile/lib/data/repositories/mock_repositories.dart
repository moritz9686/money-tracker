import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';

class MockAuthRepository implements AuthRepository {
  bool _signedIn = false;

  @override
  Future<bool> isSignedIn() async => _signedIn;

  @override
  Future<void> signIn(String email, String password) async {
    _signedIn = true;
  }

  @override
  Future<void> signUp(String email, String password) => signIn(email, password);

  @override
  String? get accessToken => null;

  @override
  Future<void> signOut() async {
    _signedIn = false;
  }
}

class MockReferenceDataRepository implements ReferenceDataRepository {
  static const food = Category(id: 'food', name: 'Food', icon: '🍽️');
  static const transport =
      Category(id: 'transport', name: 'Transport', icon: '🚕');
  static const shopping =
      Category(id: 'shopping', name: 'Shopping', icon: '🛍️');
  static const salary = Category(id: 'salary', name: 'Salary', icon: '💼');
  static const entertainment = Category(
    id: 'entertainment',
    name: 'Entertainment',
    icon: '🎬',
  );

  @override
  Future<List<FinancialAccount>> getAccounts() async => [
        FinancialAccount(
          id: 'account-1',
          name: 'Primary bank account',
          last4: '1234',
          balance: Money.fromApi('45250.00', 'INR'),
        ),
        FinancialAccount(
          id: 'account-2',
          name: 'Travel card',
          last4: '6789',
          balance: Money.fromApi('8200.00', 'INR'),
        ),
      ];

  @override
  Future<List<Category>> getCategories() async => const [
        food,
        transport,
        shopping,
        salary,
        entertainment,
      ];

}

/// Preview-only fixture data. Normal mobile builds use ApiTransactionRepository.
class MockTransactionRepository implements TransactionRepository {
  final _transactions = [
    FinancialTransaction(
      id: 'preview-1',
      merchant: 'Monthly salary',
      description: 'Salary credit',
      amount: Money.fromApi('85000.00', 'INR'),
      date: DateTime.now().subtract(const Duration(days: 1)),
      type: TransactionType.credit,
      paymentMode: PaymentMode.other,
      category: MockReferenceDataRepository.salary,
      accountName: 'Primary bank account',
    ),
    FinancialTransaction(
      id: 'preview-2',
      merchant: 'Swiggy',
      description: 'Dinner order',
      amount: Money.fromApi('540.00', 'INR'),
      date: DateTime.now().subtract(const Duration(days: 1, hours: 3)),
      type: TransactionType.debit,
      paymentMode: PaymentMode.upi,
      category: MockReferenceDataRepository.food,
      accountName: 'Primary bank account',
    ),
    FinancialTransaction(
      id: 'preview-3',
      merchant: 'Uber',
      description: 'Trip to office',
      amount: Money.fromApi('280.00', 'INR'),
      date: DateTime.now().subtract(const Duration(days: 2)),
      type: TransactionType.debit,
      paymentMode: PaymentMode.upi,
      category: MockReferenceDataRepository.transport,
      accountName: 'Primary bank account',
    ),
    FinancialTransaction(
      id: 'preview-4',
      merchant: 'Netflix',
      description: 'Monthly subscription',
      amount: Money.fromApi('649.00', 'INR'),
      date: DateTime.now().subtract(const Duration(days: 3)),
      type: TransactionType.debit,
      paymentMode: PaymentMode.card,
      category: MockReferenceDataRepository.entertainment,
      accountName: 'Travel card',
    ),
  ];

  @override
  Future<FinancialTransaction> getTransaction(String transactionId) async =>
      _transactions.firstWhere((item) => item.id == transactionId);

  @override
  Future<TransactionPage> getTransactions(TransactionQuery query) async {
    var filtered = _transactions.where((item) {
      final merchant = query.merchant?.toLowerCase() ?? '';
      return (query.transactionType == null || item.type == query.transactionType) &&
          (query.paymentMode == null || item.paymentMode == query.paymentMode) &&
          (merchant.isEmpty || (item.merchant?.toLowerCase().contains(merchant) ?? false));
    }).toList();
    filtered.sort((left, right) => query.sort == TransactionSort.desc
        ? right.date.compareTo(left.date)
        : left.date.compareTo(right.date));
    final start = query.offset.clamp(0, filtered.length);
    final end = (start + query.limit).clamp(start, filtered.length);
    return TransactionPage(
      items: filtered.sublist(start, end),
      total: filtered.length,
      limit: query.limit,
      offset: query.offset,
    );
  }
}
