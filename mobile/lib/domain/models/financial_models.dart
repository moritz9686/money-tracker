enum TransactionType { debit, credit }

enum PaymentMode { upi, card, neft, imps, rtgs, atm, cash, other }

class Money {
  const Money._(this.minorUnits, this.currency);

  factory Money.fromMinorUnits(int minorUnits, String currency) =>
      Money._(minorUnits, currency);

  factory Money.fromApi(Object value, String currency) {
    final raw = value.toString();
    final match = RegExp(r'^(-?)(\d+)(?:\.(\d{1,2}))?$').firstMatch(raw);
    if (match == null) throw const FormatException('Invalid money value');
    final fraction = (match.group(3) ?? '').padRight(2, '0');
    final units = int.parse(match.group(2)!) * 100 + int.parse(fraction);
    return Money._(match.group(1) == '-' ? -units : units, currency);
  }

  final int minorUnits;
  final String currency;
}

class Category {
  const Category({required this.id, required this.name, required this.icon});

  final String id;
  final String name;
  final String icon;
}

class FinancialAccount {
  const FinancialAccount({
    required this.id,
    required this.name,
    required this.last4,
    required this.balance,
  });

  final String id;
  final String name;
  final String last4;
  final Money balance;
}

class FinancialTransaction {
  const FinancialTransaction({
    required this.id,
    required this.merchant,
    required this.description,
    required this.amount,
    required this.date,
    required this.type,
    required this.paymentMode,
    required this.category,
    required this.accountName,
    this.bankName,
    this.accountLast4,
    this.referenceId,
  });

  final String id;
  final String? merchant;
  final String? description;
  final Money amount;
  final DateTime date;
  final TransactionType type;
  final PaymentMode paymentMode;
  final Category? category;
  final String? accountName;
  final String? bankName;
  final String? accountLast4;
  final String? referenceId;
}
