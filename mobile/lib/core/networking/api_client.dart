import 'dart:convert';
import 'dart:io';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;
}

abstract interface class ApiClient {
  Future<Map<String, dynamic>> get(String path);
}

/// Minimal HTTP client for future authenticated API calls.
/// Repositories are the only layer that should depend on this abstraction.
class HttpApiClient implements ApiClient {
  HttpApiClient({required this.baseUrl});

  final String baseUrl;

  @override
  Future<Map<String, dynamic>> get(String path) async {
    final client = HttpClient();
    try {
      final request = await client.getUrl(Uri.parse('$baseUrl$path'));
      request.headers.contentType = ContentType.json;
      final response = await request.close();
      final body = await response.transform(utf8.decoder).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException('Request failed', statusCode: response.statusCode);
      }
      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        throw const ApiException('Unexpected API response');
      }
      return decoded;
    } on SocketException {
      throw const ApiException('Unable to reach the server');
    } finally {
      client.close(force: true);
    }
  }
}
