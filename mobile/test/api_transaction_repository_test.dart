import 'package:flutter_test/flutter_test.dart';
import 'package:money_tracker_mobile/core/networking/api_client.dart';
import 'package:money_tracker_mobile/data/repositories/api_transaction_repository.dart';
import 'package:money_tracker_mobile/domain/models/financial_models.dart';
import 'package:money_tracker_mobile/domain/repositories/repositories.dart';
import 'package:money_tracker_mobile/presentation/widgets/finance_widgets.dart';

class FakeApiClient implements ApiClient {
  String? path;
  Map<String, String>? queryParameters;

  @override
  Future<Map<String, dynamic>> get(
    String requestedPath, {
    Map<String, String>? queryParameters,
  }) async {
    path = requestedPath;
    this.queryParameters = queryParameters;
    return {
      'items': [_transactionJson],
      'total': 1,
      'limit': 20,
      'offset': 0,
    };
  }
}

const _transactionJson = {
  'id': '00000000-0000-0000-0000-000000000030',
  'transaction_date': '2026-09-24T12:00:00Z',
  'amount': '500.25',
  'currency': 'INR',
  'transaction_type': 'DEBIT',
  'payment_mode': 'UPI',
  'merchant': 'Swiggy',
  'description': 'Dinner',
  'bank_name': 'Example Bank',
  'account_last4': '1234',
  'reference_id': 'REF-123',
  'category_id': null,
};

void main() {
  test('transaction repository maps a backend page and sends filters', () async {
    final client = FakeApiClient();
    final page = await ApiTransactionRepository(client).getTransactions(
      const TransactionQuery(
        limit: 20,
        offset: 0,
        transactionType: TransactionType.debit,
        paymentMode: PaymentMode.upi,
        merchant: 'swig',
      ),
    );

    expect(client.path, '/transactions');
    expect(client.queryParameters?['transaction_type'], 'DEBIT');
    expect(client.queryParameters?['payment_mode'], 'UPI');
    expect(client.queryParameters?['merchant'], 'swig');
    expect(page.total, 1);
    expect(page.items.single.amount.minorUnits, 50025);
    expect(page.items.single.merchant, 'Swiggy');
  });

  test('money formatting retains two decimal places without floating point', () {
    expect(formatMoney(Money.fromApi('500.25', 'INR')), '₹500.25');
    expect(formatMoney(Money.fromApi('-540.00', 'INR')), '-₹540');
  });
}
