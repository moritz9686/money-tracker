import 'dart:convert';
import 'dart:io';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;
}

abstract interface class ApiClient {
  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? queryParameters,
  });
}

/// Minimal HTTP client for future authenticated API calls.
/// Repositories are the only layer that should depend on this abstraction.
class HttpApiClient implements ApiClient {
  HttpApiClient({
    required this.baseUrl,
    this.headers = const {},
    HttpClient Function()? clientFactory,
  }) : _clientFactory = clientFactory ?? HttpClient.new;

  final String baseUrl;
  final Map<String, String> headers;
  final HttpClient Function() _clientFactory;

  @override
  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? queryParameters,
  }) async {
    if (baseUrl.isEmpty) {
      throw const ApiException('API_BASE_URL has not been configured');
    }
    final client = _clientFactory();
    try {
      final uri = Uri.parse(baseUrl).resolve(path).replace(
            queryParameters: queryParameters,
          );
      final request = await client.getUrl(uri);
      request.headers.contentType = ContentType.json;
      headers.forEach(request.headers.set);
      final response = await request.close().timeout(const Duration(seconds: 15));
      final body = await response.transform(utf8.decoder).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          _errorMessage(body) ?? 'Request failed',
          statusCode: response.statusCode,
        );
      }
      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        throw const ApiException('Unexpected API response');
      }
      return decoded;
    } on SocketException {
      throw const ApiException('Unable to reach the server');
    } on HttpException {
      throw const ApiException('Unable to reach the server');
    } on FormatException {
      throw const ApiException('Unexpected API response');
    } finally {
      client.close(force: true);
    }
  }

  String? _errorMessage(String body) {
    try {
      final decoded = jsonDecode(body);
      final detail = decoded is Map<String, dynamic> ? decoded['detail'] : null;
      if (detail is Map<String, dynamic> && detail['message'] is String) {
        return detail['message'] as String;
      }
    } on FormatException {
      return null;
    }
    return null;
  }
}
