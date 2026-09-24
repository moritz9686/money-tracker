import '../models/financial_models.dart';

abstract interface class AuthRepository {
  Future<bool> isSignedIn();
  Future<void> signInForDevelopment();
  Future<void> signOut();
}

abstract interface class TransactionRepository {
  Future<List<FinancialTransaction>> getTransactions();
  Future<List<FinancialAccount>> getAccounts();
  Future<List<Category>> getCategories();
}
