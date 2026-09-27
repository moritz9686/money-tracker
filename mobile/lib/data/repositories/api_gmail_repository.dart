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
}
