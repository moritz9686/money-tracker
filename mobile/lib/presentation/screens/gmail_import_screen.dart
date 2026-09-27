import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';

class GmailImportScreen extends StatefulWidget {
  const GmailImportScreen({
    required this.gmailRepository,
    required this.referenceDataRepository,
    super.key,
  });

  final GmailRepository gmailRepository;
  final ReferenceDataRepository referenceDataRepository;

  @override
  State<GmailImportScreen> createState() => _GmailImportScreenState();
}

class _GmailImportScreenState extends State<GmailImportScreen> {
  late final Future<List<FinancialAccount>> _accounts;
  String? _selectedAccountId;
  bool _opening = false;
  bool _authorizationOpened = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _accounts = widget.referenceDataRepository.getAccounts();
  }

  Future<void> _connect() async {
    final accountId = _selectedAccountId;
    if (accountId == null) return;
    setState(() {
      _opening = true;
      _error = null;
    });
    try {
      final uri = await widget.gmailRepository.createAuthorizationUrl(accountId);
      final launched = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
        webOnlyWindowName: '_blank',
      );
      if (!launched) throw StateError('Google authorization could not be opened');
      if (mounted) setState(() => _authorizationOpened = true);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not start Gmail import. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _opening = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Import from Gmail')),
        body: FutureBuilder<List<FinancialAccount>>(
          future: _accounts,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return const Center(child: Text('Could not load your accounts.'));
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final accounts = snapshot.data!;
            if (accounts.isEmpty) {
              return const Padding(
                padding: EdgeInsets.all(24),
                child: Center(
                  child: Text('Create a financial account before importing Gmail transactions.'),
                ),
              );
            }
            _selectedAccountId ??= accounts.first.id;
            return ListView(
              padding: const EdgeInsets.all(24),
              children: [
                const Icon(Icons.mail_outline, size: 64),
                const SizedBox(height: 20),
                Text('Import transaction emails', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 12),
                const Text(
                  'Google will ask for read-only Gmail access. The server scans likely transaction alerts once and does not store your Gmail password, access token, or raw emails.',
                ),
                const SizedBox(height: 24),
                DropdownButtonFormField<String>(
                  initialValue: _selectedAccountId,
                  decoration: const InputDecoration(labelText: 'Save transactions to'),
                  items: accounts
                      .map((account) => DropdownMenuItem(value: account.id, child: Text(account.name)))
                      .toList(growable: false),
                  onChanged: _opening ? null : (value) => setState(() => _selectedAccountId = value),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: _opening ? null : _connect,
                  icon: const Icon(Icons.open_in_new),
                  label: Text(_opening ? 'Opening Google…' : 'Connect and import'),
                ),
                if (_authorizationOpened) ...[
                  const SizedBox(height: 24),
                  const Text(
                    'Finish Google authorization in the new tab. When it reports “completed”, return here.',
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).pop(true),
                    child: const Text('Authorization completed — refresh transactions'),
                  ),
                ],
              ],
            );
          },
        ),
      );
}
