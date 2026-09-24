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
