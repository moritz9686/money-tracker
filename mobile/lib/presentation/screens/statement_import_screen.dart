import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

class StatementImportScreen extends StatefulWidget {
  const StatementImportScreen({super.key});

  @override
  State<StatementImportScreen> createState() => _StatementImportScreenState();
}

class _StatementImportScreenState extends State<StatementImportScreen> {
  static const _maximumBytes = 15 * 1024 * 1024;
  PlatformFile? _file;
  String? _error;
  bool _uploading = false;

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'csv', 'xlsx'],
      withData: false,
    );
    if (result == null) return;
    final file = result.files.single;
    if (file.size > _maximumBytes) {
      setState(() => _error = 'Choose a statement smaller than 15 MB.');
      return;
    }
    setState(() { _file = file; _error = null; });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Import statement')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.upload_file_outlined, size: 64),
              const SizedBox(height: 16),
              const Text(
                'Choose a PDF, CSV, or XLSX bank statement. The original file is uploaded only for parsing and is not retained.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              OutlinedButton.icon(onPressed: _uploading ? null : _pickFile, icon: const Icon(Icons.folder_open), label: const Text('Choose statement')),
              if (_file != null) ListTile(leading: const Icon(Icons.description_outlined), title: Text(_file!.name), subtitle: Text('${(_file!.size / 1024).ceil()} KB')),
              if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
              if (_uploading) const Padding(padding: EdgeInsets.only(top: 16), child: Column(children: [LinearProgressIndicator(), SizedBox(height: 8), Text('Uploading and parsing securely…')])),
              const Spacer(),
              FilledButton(onPressed: _file == null || _uploading ? null : () => setState(() => _error = 'Statement preview API is not available yet.'), child: const Text('Preview transactions')),
            ],
          ),
        ),
      );
}
