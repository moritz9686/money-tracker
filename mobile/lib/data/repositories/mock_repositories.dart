import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';

class MockAuthRepository implements AuthRepository {
  bool _signedIn = false;

  @override
  Future<bool> isSignedIn() async => _signedIn;

  @override
  Future<void> signInForDevelopment() async {
    _signedIn = true;
  }

  @override
  Future<void> signOut() async {
    _signedIn = false;
  }
}

class MockTransactionRepository implements TransactionRepository {
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
  Future<List<FinancialAccount>> getAccounts() async => const [
        FinancialAccount(
          id: 'account-1',
          name: 'Primary bank account',
          last4: '1234',
          balance: 45250,
        ),
        FinancialAccount(
          id: 'account-2',
          name: 'Travel card',
          last4: '6789',
          balance: 8200,
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

  @override
  Future<List<FinancialTransaction>> getTransactions() async => [
        FinancialTransaction(
          id: 'transaction-1',
          merchant: 'Monthly salary',
          description: 'Salary credit',
          amount: 85000,
          date: DateTime.now().subtract(const Duration(days: 1)),
          type: TransactionType.credit,
          paymentMode: PaymentMode.other,
          category: salary,
          accountName: 'Primary bank account',
        ),
        FinancialTransaction(
          id: 'transaction-2',
          merchant: 'Swiggy',
          description: 'Dinner order',
          amount: 540,
          date: DateTime.now().subtract(const Duration(days: 1, hours: 3)),
          type: TransactionType.debit,
          paymentMode: PaymentMode.upi,
          category: food,
          accountName: 'Primary bank account',
        ),
        FinancialTransaction(
          id: 'transaction-3',
          merchant: 'Uber',
          description: 'Trip to office',
          amount: 280,
          date: DateTime.now().subtract(const Duration(days: 2)),
          type: TransactionType.debit,
          paymentMode: PaymentMode.upi,
          category: transport,
          accountName: 'Primary bank account',
        ),
        FinancialTransaction(
          id: 'transaction-4',
          merchant: 'Netflix',
          description: 'Monthly subscription',
          amount: 649,
          date: DateTime.now().subtract(const Duration(days: 3)),
          type: TransactionType.debit,
          paymentMode: PaymentMode.card,
          category: entertainment,
          accountName: 'Travel card',
        ),
        FinancialTransaction(
          id: 'transaction-5',
          merchant: 'Amazon',
          description: 'Household order',
          amount: 1250,
          date: DateTime.now().subtract(const Duration(days: 4)),
          type: TransactionType.debit,
          paymentMode: PaymentMode.card,
          category: shopping,
          accountName: 'Primary bank account',
        ),
      ];
}
