import '../models/financial_models.dart';

abstract interface class AuthRepository {
  Future<bool> isSignedIn();
  Future<void> signIn(String email, String password);
  Future<void> signUp(String email, String password);
  Future<void> signOut();
  String? get accessToken;
}

abstract interface class TransactionRepository {
  Future<TransactionPage> getTransactions(TransactionQuery query);
  Future<FinancialTransaction> getTransaction(String transactionId);
}

class TransactionQuery {
  const TransactionQuery({
    this.limit = 20,
    this.offset = 0,
    this.startDate,
    this.endDate,
    this.transactionType,
    this.paymentMode,
    this.categoryId,
    this.bankName,
    this.accountId,
    this.merchant,
    this.sort = TransactionSort.desc,
  });

  final int limit;
  final int offset;
  final DateTime? startDate;
  final DateTime? endDate;
  final TransactionType? transactionType;
  final PaymentMode? paymentMode;
  final String? categoryId;
  final String? bankName;
  final String? accountId;
  final String? merchant;
  final TransactionSort sort;

  Map<String, String> toQueryParameters() => {
        'limit': '$limit',
        'offset': '$offset',
        if (startDate != null) 'start_date': startDate!.toUtc().toIso8601String(),
        if (endDate != null) 'end_date': endDate!.toUtc().toIso8601String(),
        if (transactionType != null) 'transaction_type': transactionType!.name.toUpperCase(),
        if (paymentMode != null) 'payment_mode': paymentMode!.name.toUpperCase(),
        if (categoryId != null && categoryId!.isNotEmpty) 'category_id': categoryId!,
        if (bankName != null && bankName!.isNotEmpty) 'bank_name': bankName!,
        if (accountId != null && accountId!.isNotEmpty) 'account_id': accountId!,
        if (merchant != null && merchant!.isNotEmpty) 'merchant': merchant!,
        'sort': sort.name,
      };
}

enum TransactionSort { asc, desc }

class TransactionPage {
  const TransactionPage({
    required this.items,
    required this.total,
    required this.limit,
    required this.offset,
  });

  final List<FinancialTransaction> items;
  final int total;
  final int limit;
  final int offset;
  bool get hasMore => offset + items.length < total;
}

abstract interface class ReferenceDataRepository {
  Future<List<FinancialAccount>> getAccounts();
  Future<List<Category>> getCategories();
}
