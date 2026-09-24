import '../../core/networking/api_client.dart';
import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';

class ApiTransactionRepository implements TransactionRepository {
  ApiTransactionRepository(this._client);

  final ApiClient _client;

  @override
  Future<TransactionPage> getTransactions(TransactionQuery query) async {
    final response = await _client.get(
      '/transactions',
      queryParameters: query.toQueryParameters(),
    );
    final rawItems = response['items'];
    if (rawItems is! List) throw const ApiException('Unexpected API response');
    return TransactionPage(
      items: rawItems.map(_transactionFromJson).toList(growable: false),
      total: _asInt(response['total']),
      limit: _asInt(response['limit']),
      offset: _asInt(response['offset']),
    );
  }

  @override
  Future<FinancialTransaction> getTransaction(String transactionId) async =>
      _transactionFromJson(await _client.get('/transactions/$transactionId'));

  FinancialTransaction _transactionFromJson(Object? value) {
    if (value is! Map<String, dynamic>) {
      throw const ApiException('Unexpected API response');
    }
    final categoryId = value['category_id'] as String?;
    return FinancialTransaction(
      id: _asString(value['id']),
      merchant: value['merchant'] as String?,
      description: value['description'] as String?,
      amount: Money.fromApi(value['amount'], _asString(value['currency'])),
      date: DateTime.parse(_asString(value['transaction_date'])),
      type: _transactionType(value['transaction_type']),
      paymentMode: _paymentMode(value['payment_mode']),
      category: categoryId == null
          ? null
          : Category(id: categoryId, name: 'Categorized', icon: '🏷️'),
      accountName: null,
      bankName: value['bank_name'] as String?,
      accountLast4: value['account_last4'] as String?,
      referenceId: value['reference_id'] as String?,
    );
  }

  int _asInt(Object? value) => switch (value) {
        int parsed => parsed,
        num parsed => parsed.toInt(),
        String parsed => int.parse(parsed),
        _ => throw const ApiException('Unexpected API response'),
      };

  String _asString(Object? value) {
    if (value is String && value.isNotEmpty) return value;
    throw const ApiException('Unexpected API response');
  }

  TransactionType _transactionType(Object? value) => switch (value) {
        'DEBIT' => TransactionType.debit,
        'CREDIT' => TransactionType.credit,
        _ => throw const ApiException('Unexpected transaction type'),
      };

  PaymentMode _paymentMode(Object? value) => switch (value) {
        'UPI' => PaymentMode.upi,
        'CARD' => PaymentMode.card,
        'NEFT' => PaymentMode.neft,
        'IMPS' => PaymentMode.imps,
        'RTGS' => PaymentMode.rtgs,
        'ATM' => PaymentMode.atm,
        'CASH' => PaymentMode.cash,
        'OTHER' => PaymentMode.other,
        _ => throw const ApiException('Unexpected payment mode'),
      };
}
