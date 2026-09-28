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
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(22),
          color: color.withValues(alpha: 0.10),
        ),
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
    final color = _breakdownColor(label);
    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(11)),
                child: Icon(_breakdownIcon(label), size: 18, color: color),
              ),
              const SizedBox(width: 10),
              Expanded(child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700))),
              Text(formatMoney(Money.fromMinorUnits(amount, 'INR')), style: const TextStyle(fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(value: fraction, minHeight: 7, color: color, backgroundColor: color.withValues(alpha: 0.12)),
          ),
        ],
      ),
    );
  }
}

IconData _breakdownIcon(String label) => switch (label.toLowerCase()) {
      'food' => Icons.restaurant_rounded,
      'transport' => Icons.directions_car_filled_rounded,
      'shopping' => Icons.shopping_bag_rounded,
      'entertainment' => Icons.movie_rounded,
      'upi' => Icons.qr_code_rounded,
      'card' => Icons.credit_card_rounded,
      _ => Icons.auto_graph_rounded,
    };

Color _breakdownColor(String label) => switch (label.toLowerCase()) {
      'food' => const Color(0xfff97316),
      'transport' => const Color(0xff0ea5e9),
      'shopping' => const Color(0xffa855f7),
      'entertainment' => const Color(0xffec4899),
      'upi' => const Color(0xff16a34a),
      'card' => const Color(0xff2563eb),
      _ => const Color(0xff6750e8),
    };

class EmptyState extends StatelessWidget {
  const EmptyState({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.auto_graph_rounded, size: 48, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
}
