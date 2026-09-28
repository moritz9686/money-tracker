import '../../core/networking/api_client.dart';
import '../../domain/repositories/repositories.dart';

class ApiGmailRepository implements GmailRepository {
  ApiGmailRepository(this._client);

  final ApiClient _client;

  @override
  Future<Uri> createAuthorizationUrl(String accountId) async {
    final response = await _client.get(
      '/gmail/authorize',
      queryParameters: {'account_id': accountId},
    );
    final rawUrl = response['authorization_url'];
    final uri = rawUrl is String ? Uri.tryParse(rawUrl) : null;
    if (uri == null || uri.scheme != 'https') {
      throw const ApiException('Invalid Gmail authorization response');
    }
    return uri;
  }

  @override
  Future<GmailSyncResult> sync() async {
    final response = await _client.post('/gmail/sync');
    final imported = response['imported'];
    final reauthorizationRequired = response['reauthorization_required'];
    if (imported is! int || reauthorizationRequired is! int) {
      throw const ApiException('Unexpected Gmail sync response');
    }
    return GmailSyncResult(
      imported: imported,
      reauthorizationRequired: reauthorizationRequired,
    );
  }
}
