import React, { useState } from 'react';

// Main App component
const App = () => {
    // State variables for the application
    const [payloadType, setPayloadType] = useState('financial'); // 'financial' or 'insurance'
    const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000'); // Default FastAPI endpoint
    const [malformations, setMalformations] = useState({
        missingRequired: false,
        invalidDataType: false,
        invalidFormat: false,
        extraField: false,
        corruptJson: false,
    });
    const [generatedPayload, setGeneratedPayload] = useState(''); // Displays the generated payload
    const [apiResponse, setApiResponse] = useState(''); // Displays the API response
    const [loading, setLoading] = useState(false); // Loading state for API calls

    // Base payloads for well-formed data
    const baseFinancialPayload = {
        transaction_id: 'FT-' + Date.now().toString().slice(-6),
        timestamp: new Date().toISOString(),
        amount: Math.round(Math.random() * 10000) / 100, // Two decimal places
        currency: 'USD',
        description: 'Online purchase',
        user_id: 'user-' + Math.floor(Math.random() * 1000),
    };

    const baseInsurancePayload = {
        claim_id: 'IC-' + Date.now().toString().slice(-6),
        policy_number: 'POL-' + Math.floor(Math.random() * 10000),
        claim_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
        claim_amount: Math.round(Math.random() * 50000) / 100,
        claim_type: 'Auto',
        insured_name: 'John Doe',
        status: 'Pending',
    };

    /**
     * Generates a payload based on the selected type and malformations.
     * @returns {Object} The generated payload.
     */
    const generatePayload = () => {
        let payload = payloadType === 'financial' ? { ...baseFinancialPayload } : { ...baseInsurancePayload };

        if (malformations.missingRequired) {
            // Remove a required field (e.g., amount for financial, claim_type for insurance)
            if (payloadType === 'financial') {
                delete payload.amount;
            } else {
                delete payload.claim_type;
            }
        }

        if (malformations.invalidDataType) {
            // Change data type (e.g., amount to string, claim_amount to boolean)
            if (payloadType === 'financial') {
                payload.amount = 'one hundred dollars';
            } else {
                payload.claim_amount = true;
            }
        }

        if (malformations.invalidFormat) {
            // Change format (e.g., timestamp to invalid date string, claim_date to invalid format)
            if (payloadType === 'financial') {
                payload.timestamp = '2023-13-40T00:00:00Z'; // Invalid month/day
            } else {
                payload.claim_date = '2023/01/01'; // Invalid date format
            }
        }

        if (malformations.extraField) {
            // Add an unexpected field
            payload.unexpected_field = 'This field should not be here.';
        }

        return payload;
    };

    /**
     * Handles the change in malformation checkboxes.
     * @param {Object} event - The checkbox change event.
     */
    const handleMalformationChange = (event) => {
        const { name, checked } = event.target;
        setMalformations(prev => ({ ...prev, [name]: checked }));
    };

    /**
     * Sends the generated payload to the FastAPI ingestor.
     */
    const sendPayload = async () => {
        const payload = generatePayload();
        let payloadToSend = payload;
        
        // Handle corrupt JSON specifically
        if (malformations.corruptJson) {
            payloadToSend = JSON.stringify(payload) + '}{'; // Intentionally malformed JSON string
        } else {
            payloadToSend = JSON.stringify(payload);
        }

        setGeneratedPayload(JSON.stringify(payload, null, 2)); // Prettify for display
        setLoading(true);
        setApiResponse('Sending payload...');

        try {
            const url = payloadType === 'financial'
                ? `${apiEndpoint}/ingest-financial-transaction/`
                : `${apiEndpoint}/ingest-insurance-claim/`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: malformations.corruptJson ? payloadToSend : JSON.stringify(payload),
            });

            const text = await response.text(); // Get raw text to handle potential non-JSON responses

            let responseBody;
            try {
                // Try parsing as JSON if Content-Type is application/json or if it looks like JSON
                if (response.headers.get('content-type')?.includes('application/json') || text.startsWith('{') || text.startsWith('[')) {
                    responseBody = JSON.parse(text);
                } else {
                    responseBody = text; // Keep as text if not JSON
                }
            } catch (jsonError) {
                // If JSON parsing fails, it's likely just plain text or malformed JSON from the server
                responseBody = text;
            }

            // Determine likely termination point based on HTTP status code
            let terminationPoint = '';
            if (response.status >= 200 && response.status < 300) {
                terminationPoint = 'API (FastAPI) accepted payload (HTTP 2xx). Check Kafka/Spark logs for further processing.';
            } else if (response.status === 422) {
                terminationPoint = 'API (FastAPI) rejected due to validation error (HTTP 422). Payload likely malformed against Pydantic schema.';
            } else if (response.status >= 400 && response.status < 500) {
                terminationPoint = `API (FastAPI) rejected (HTTP ${response.status}). Client-side error.`;
            } else if (response.status >= 500) {
                terminationPoint = `API (FastAPI) encountered server error (HTTP ${response.status}). Check FastAPI application logs.`;
            } else {
                terminationPoint = `Unexpected API response (HTTP ${response.status}).`;
            }

            setApiResponse(
                `Status: ${response.status}\n` +
                `Termination Point: ${terminationPoint}\n` +
                `Response Body:\n${JSON.stringify(responseBody, null, 2)}`
            );

        } catch (error) {
            setApiResponse(`Error sending payload: ${error.message}\nTermination Point: Network/Connection Issue (Payload not reaching API).`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-4 font-inter">
            <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-xl p-6">
                <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Data Payload Generator for Edge Cases</h1>

                {/* API Endpoint Configuration */}
                <div className="mb-6 p-4 border border-gray-200 rounded-lg">
                    <label htmlFor="apiEndpoint" className="block text-lg font-medium text-gray-700 mb-2">
                        FastAPI Ingestor Endpoint:
                    </label>
                    <input
                        type="text"
                        id="apiEndpoint"
                        value={apiEndpoint}
                        onChange={(e) => setApiEndpoint(e.target.value)}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="e.g., http://localhost:8000"
                    />
                </div>

                {/* Payload Type Selection */}
                <div className="mb-6 p-4 border border-gray-200 rounded-lg">
                    <label className="block text-lg font-medium text-gray-700 mb-2">
                        Select Payload Type:
                    </label>
                    <div className="flex space-x-4">
                        <label className="inline-flex items-center">
                            <input
                                type="radio"
                                name="payloadType"
                                value="financial"
                                checked={payloadType === 'financial'}
                                onChange={() => setPayloadType('financial')}
                                className="form-radio text-blue-600 rounded-full"
                            />
                            <span className="ml-2 text-gray-700">Financial Transaction</span>
                        </label>
                        <label className="inline-flex items-center">
                            <input
                                type="radio"
                                name="payloadType"
                                value="insurance"
                                checked={payloadType === 'insurance'}
                                onChange={() => setPayloadType('insurance')}
                                className="form-radio text-blue-600 rounded-full"
                            />
                            <span className="ml-2 text-gray-700">Insurance Claim</span>
                        </label>
                    </div>
                </div>

                {/* Malformation Options */}
                <div className="mb-6 p-4 border border-gray-200 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-700 mb-2">Introduce Malformations:</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <label className="inline-flex items-center">
                            <input
                                type="checkbox"
                                name="missingRequired"
                                checked={malformations.missingRequired}
                                onChange={handleMalformationChange}
                                className="form-checkbox text-blue-600 rounded"
                            />
                            <span className="ml-2 text-gray-700">Missing Required Field</span>
                        </label>
                        <label className="inline-flex items-center">
                            <input
                                type="checkbox"
                                name="invalidDataType"
                                checked={malformations.invalidDataType}
                                onChange={handleMalformationChange}
                                className="form-checkbox text-blue-600 rounded"
                            />
                            <span className="ml-2 text-gray-700">Invalid Data Type</span>
                        </label>
                        <label className="inline-flex items-center">
                            <input
                                type="checkbox"
                                name="invalidFormat"
                                checked={malformations.invalidFormat}
                                onChange={handleMalformationChange}
                                className="form-checkbox text-blue-600 rounded"
                            />
                            <span className="ml-2 text-gray-700">Invalid Format (e.g., Date/Time)</span>
                        </label>
                        <label className="inline-flex items-center">
                            <input
                                type="checkbox"
                                name="extraField"
                                checked={malformations.extraField}
                                onChange={handleMalformationChange}
                                className="form-checkbox text-blue-600 rounded"
                            />
                            <span className="ml-2 text-gray-700">Extra/Unexpected Field</span>
                        </label>
                        <label className="inline-flex items-center">
                            <input
                                type="checkbox"
                                name="corruptJson"
                                checked={malformations.corruptJson}
                                onChange={handleMalformationChange}
                                className="form-checkbox text-blue-600 rounded"
                            />
                            <span className="ml-2 text-gray-700">Corrupt JSON (non-parseable string)</span>
                        </label>
                    </div>
                </div>

                {/* Generate & Send Button */}
                <button
                    onClick={sendPayload}
                    disabled={loading}
                    className={`w-full py-3 px-6 rounded-lg text-white font-semibold shadow-md transition duration-300 ${
                        loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                    }`}
                >
                    {loading ? 'Sending...' : 'Generate & Send Payload'}
                </button>

                {/* Generated Payload Display */}
                <div className="mt-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-2">Generated Payload:</h2>
                    <pre className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                        {generatedPayload || 'Payload will appear here after generation.'}
                    </pre>
                </div>

                {/* API Response Display */}
                <div className="mt-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-2">API Response:</h2>
                    <pre className="bg-gray-800 text-yellow-300 p-4 rounded-lg overflow-x-auto text-sm">
                        {apiResponse || 'API response will appear here.'}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default App;
