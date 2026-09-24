enum TransactionType { debit, credit }

enum PaymentMode { upi, card, neft, imps, rtgs, atm, cash, other }

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
  final int balance;
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
  });

  final String id;
  final String merchant;
  final String description;
  final int amount;
  final DateTime date;
  final TransactionType type;
  final PaymentMode paymentMode;
  final Category category;
  final String accountName;
}
