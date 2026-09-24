import 'package:flutter/material.dart';

String formatInr(int amount) {
  final digits = amount.abs().toString();
  final reversed = digits.split('').reversed.toList();
  final parts = <String>[];
  for (var index = 0; index < reversed.length; index += 3) {
    parts.add(reversed.skip(index).take(3).toList().reversed.join());
  }
  return '${amount.isNegative ? '-' : ''}₹${parts.reversed.join(',')}';
}

class SummaryCard extends StatelessWidget {
  const SummaryCard({
    required this.label,
    required this.amount,
    required this.color,
    super.key,
  });

  final String label;
  final int amount;
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
                formatInr(amount),
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
              Text(formatInr(amount)),
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
