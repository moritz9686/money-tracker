import 'package:flutter_test/flutter_test.dart';
import 'package:money_tracker_mobile/data/repositories/mock_repositories.dart';
import 'package:money_tracker_mobile/domain/models/financial_models.dart';
import 'package:money_tracker_mobile/presentation/widgets/finance_widgets.dart';

void main() {
  test('mock transactions contain both credits and debits', () async {
    final transactions = await MockTransactionRepository().getTransactions();

    expect(
      transactions.any((item) => item.type == TransactionType.credit),
      isTrue,
    );
    expect(
      transactions.any((item) => item.type == TransactionType.debit),
      isTrue,
    );
  });

  test('currency formatting does not use fractional money values', () {
    expect(formatInr(85000), '₹85,000');
    expect(formatInr(-540), '-₹540');
  });
}
