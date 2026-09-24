import 'package:flutter/material.dart';

import '../../domain/models/financial_models.dart';

String formatMoney(Money amount) {
  final whole = amount.minorUnits ~/ 100;
  final digits = whole.abs().toString();
  final reversed = digits.split('').reversed.toList();
  final parts = <String>[];
  for (var index = 0; index < reversed.length; index += 3) {
    parts.add(reversed.skip(index).take(3).toList().reversed.join());
  }
  final fractional = amount.minorUnits.abs() % 100;
  final suffix = fractional == 0 ? '' : '.${fractional.toString().padLeft(2, '0')}';
  return '${amount.minorUnits.isNegative ? '-' : ''}₹${parts.reversed.join(',')}$suffix';
}

class SummaryCard extends StatelessWidget {
  const SummaryCard({
    required this.label,
    required this.amount,
    required this.color,
    super.key,
  });

  final String label;
  final Money amount;
  final Color color;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              Text(
                formatMoney(amount),
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
        ),
      );
}

class BreakdownRow extends StatelessWidget {
  const BreakdownRow({
    required this.label,
    required this.amount,
    required this.total,
    super.key,
  });

  final String label;
  final int amount;
  final int total;

  @override
  Widget build(BuildContext context) {
    final fraction = total == 0 ? 0.0 : amount / total;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: Text(label)),
              Text(formatMoney(Money.fromMinorUnits(amount, 'INR'))),
            ],
          ),
          const SizedBox(height: 5),
          LinearProgressIndicator(value: fraction, minHeight: 7),
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(message, textAlign: TextAlign.center),
        ),
      );
}
