(function($) {
    // Wait for the DOM to be fully loaded
    $(document).ready(function() {
        console.log("AI Service Config Admin JS loaded");
        
        // Provider data for STT
        const sttProviders = {
            'whisper': {
                'model_versions': [
                    ['whisper-1', 'Whisper-1'],
                    ['whisper-large-v2', 'Whisper-Large-V2'],
                    ['whisper-large-v3', 'Whisper-Large-V3']
                ]
            },
            'sarvam_ai': {
                'model_versions': [
                    ['saarika:v2', 'Saarika:V2']
                    // ['saaras:v2', 'Saaras:V2'],
                    // ['saaras:turbo', 'Saaras:Turbo'],
                    // ['saaras:flash', 'Saaras:Flash']
                ]
            }
        };
        
        // Provider data for Translation
        const translationProviders = {
            'sarvam_ai': {
                'model_versions': [
                    ['mayura:v1', 'Mayura:V1']
                ]
            }
        };
        
        // Provider data for TTS
        const ttsProviders = {
            'parler_tts': {
                'model_versions': [],
                'voices': [
                    ['Divya', 'Divya'],
                    ['Anjali', 'Anjali'],
                    ['Rohit', 'Rohit']
                ]
            },
            'smallest_ai': {
                'model_versions': [
                    ['lightning', 'Lightning'],
                    ['lightning-large', 'Lightning Large']
                ],
                'voices': [
                    ['chetan', 'Chetan'],
                    ['arnav', 'Arnav'],
                    ['abhinav', 'Abhinav'],
                    ['sushma', 'Sushma']
                ]
            },
            'sarvam_ai': {
                'model_versions': [
                    ['bulbul:v1', 'Bulbul:V1']
                ],
                'voices': [
                    ['meera', 'Meera'],
                    ['maitreyi', 'Maitreyi'],
                    ['arvind', 'Arvind'],
                    ['arjun', 'Arjun']
                ]
            }
        };
        
        // Provider data for LLM
        const llmProviders = {
            'openai': {
                'model_versions': [
                    ['gpt-4o', 'GPT-4o'],
                    ['gpt-4o-mini', 'GPT-4o Mini'],
                    ['gpt-4-turbo', 'GPT-4 Turbo']
                ]
            },
            'gemini': {
                'model_versions': [
                    ['gemini-1.5-flash', 'Gemini 1.5 Flash']
                ]
            },
            'anthropic': {
                'model_versions': [
                    ['claude-3-sonnet', 'Claude 3 Sonnet'],
                    ['claude-3-haiku', 'Claude 3 Haiku']
                ]
            },
            'chatgroq': {
                'model_versions': [["qwen-2.5-32b", "Qwen-2.5-32B"]]
            }
        };

        // Provider descriptions
        const providerDescriptions = {
            // STT providers
            'whisper': "OpenAI Whisper provides robust ASR capabilities supporting multiple languages 90+.",
            'sarvam_ai_stt': "Sarvam.ai supports multilingual ASR with optimized models for Indian languages, supports translation to text of the spoken language and also has a feature of direct English translation",
            
            // Translation providers
            'sarvam_ai_translation': "Sarvam.ai provides both Indic to English and English to Indic.",
            
            // TTS providers
            'parler_tts': "Parler TTS automatically detects language, the speaker option you choose goes to description of voice",
            'smallest_ai': "Smallest.ai Waves supports Hindi, English fluently, other languages are possible as well.",
            'sarvam_ai_tts': "Sarvam.ai supports 10 languages, supports 3 texts in a single Api call, each text<500 characters",
            
            // LLM providers
            'openai': "OpenAI offers various GPT models with different capabilities and pricing.",
            'gemini': "Google Gemini provides multimodal AI capabilities with competitive performance.",
            'anthropic': "Anthropic Claude models are designed with a focus on safety and helpfulness.",
            'chatgroq': "ChatGroq offers open-source models optimized for performance."
        };

        const temperatureDescriptions = {
            '0.0': 'Deterministic: The model always returns the most likely response.',
            '0.3': 'Low Creativity: Responses are mostly predictable but with slight variation.',
            '0.7': 'Balanced: Mix of predictability and creativity in responses.',
            '1.0': 'Creative: More diverse and exploratory responses, less deterministic.'
        };

        // Debug: Log all form fields to see if they exist
        console.log("STT Provider select exists:", $('#stt_provider_select').length);
        console.log("Translation Provider select exists:", $('#translation_provider_select').length);
        console.log("TTS Provider select exists:", $('#tts_provider_select').length);
        console.log("LLM Provider select exists:", $('#llm_provider_select').length);
        console.log("Temperature input exists:", $('#temperature_input').length);

        // Helper function to get the stored value from an input
        function getStoredValue(selector) {
            const field = $(selector);
            // Try different ways to get the stored value
            return field.data('initial-value') || 
                   field.attr('data-initial-value') || 
                   field.val();
        }

        // Function to update model version options for STT
        function updateSTTModelVersionOptions(provider) {
            console.log("Updating STT model version options for provider:", provider);
            updateSelectOptions($('#stt_model_version_select'), sttProviders, provider, 'model_versions');
        }

        // Function to update model version options for Translation
        function updateTranslationModelVersionOptions(provider) {
            console.log("Updating Translation model version options for provider:", provider);
            updateSelectOptions($('#translation_model_version_select'), translationProviders, provider, 'model_versions');
        }

        // Function to update model version and voice options for TTS
        function updateTTSOptions(provider) {
            console.log("Updating TTS options for provider:", provider);
            updateSelectOptions($('#tts_model_version_select'), ttsProviders, provider, 'model_versions');
            updateSelectOptions($('#tts_voice_select'), ttsProviders, provider, 'voices');
        }

        // Function to update model version options for LLM
        function updateLLMModelVersionOptions(provider) {
            console.log("Updating LLM model version options for provider:", provider);
            updateSelectOptions($('#llm_model_version_select'), llmProviders, provider, 'model_versions');
        }

        // Modified helper function to update select options
        function updateSelectOptions(selectElement, providerData, provider, optionType) {
            // Try to find element by ID, and if not found, by name
            if (selectElement.length === 0) {
                const selectName = selectElement.attr('id').replace('_select', '');
                selectElement = $(`select[name="${selectName}"]`);
                if (selectElement.length === 0) {
                    console.error(`Select element for ${selectName} not found!`);
                    return;
                }
            }
            
            // Store the current value before modifying the options
            const currentValue = selectElement.val();
            console.log(`Current value for ${selectElement.attr('id')}: ${currentValue}`);
            
            // Check if there's a hidden input storing the initial value
            const hiddenInput = $(`input[type="hidden"][name="${selectElement.attr('name')}"]`);
            const hiddenValue = hiddenInput.length > 0 ? hiddenInput.val() : null;
            console.log(`Hidden value for ${selectElement.attr('id')}: ${hiddenValue}`);

            selectElement.empty();
            
            // Add empty option for null value
            selectElement.append($('<option>', {
                value: '',
                text: '--------'
            }));
            
            // Add options based on selected provider
            if (provider && providerData[provider] && providerData[provider][optionType]) {
                const options = providerData[provider][optionType];
                console.log(`Found ${options.length} ${optionType} for provider ${provider}`);
                
                options.forEach(function(option) {
                    const optionElement = $('<option>', {
                        value: option[0],
                        text: option[1]
                    });
                    
                    selectElement.append(optionElement);
                });
                
                // If no options available for this provider
                if (options.length === 0) {
                    selectElement.append($('<option>', {
                        value: 'default',
                        text: 'Default'
                    }));
                }
            }

            // Attempt to restore the value using various methods
            console.log(`Attempting to restore value for ${selectElement.attr('id')}`);
            
            // Try the current value first
            if (currentValue && currentValue.length > 0) {
                console.log(`Restoring current value: ${currentValue}`);
                selectElement.val(currentValue);
            } 
            // Then try the hidden value
            else if (hiddenValue && hiddenValue.length > 0) {
                console.log(`Restoring hidden value: ${hiddenValue}`);
                selectElement.val(hiddenValue);
            }
            
            // If still no value is selected but we have options, check if the value exists in the options
            if (!selectElement.val() && provider && providerData[provider] && providerData[provider][optionType]) {
                const options = providerData[provider][optionType];
                
                // Get the initial value from the data attribute if available
                const initialValue = selectElement.data('initial-value');
                console.log(`Initial value from data attribute: ${initialValue}`);
                
                if (initialValue) {
                    const matchingOption = options.find(option => option[0] === initialValue);
                    if (matchingOption) {
                        console.log(`Setting initial value: ${initialValue}`);
                        selectElement.val(initialValue);
                    }
                }
            }
            
            // If we still don't have a value selected, but we should, log it as an error
            if (provider && !selectElement.val() && currentValue) {
                console.error(`Failed to restore value for ${selectElement.attr('id')}. Expected: ${currentValue}`);
            }
        }

        // Helper function to setup description areas
        function setupDescriptionArea(fieldId, className) {
            const field = $(fieldId).closest('.form-row');
            if (field.length === 0) {
                console.error(`Field row for ${fieldId} not found!`);
                return;
            }
            
            // Check if description div already exists
            let descriptionDiv = field.find(`.${className}`);
            if (descriptionDiv.length === 0) {
                console.log(`Creating new ${className} div`);
                descriptionDiv = $(`<div class="${className}" style="margin-left: 170px; color: #666; font-style: italic;"></div>`);
                field.append(descriptionDiv);
            }
            
            return descriptionDiv;
        }

        // Functions to update provider descriptions
        function updateSTTProviderDescription(provider) {
            const descriptionDiv = setupDescriptionArea('#stt_provider_select', 'stt-provider-description');
            if (!descriptionDiv) return;
            
            const description = providerDescriptions[provider] || 
                                providerDescriptions[provider + '_stt'] || 
                                'No description available.';
            console.log("Setting STT provider description:", description);
            descriptionDiv.text(description);
        }

        function updateTranslationProviderDescription(provider) {
            const descriptionDiv = setupDescriptionArea('#translation_provider_select', 'translation-provider-description');
            if (!descriptionDiv) return;
            
            const description = providerDescriptions[provider] || 
                                providerDescriptions[provider + '_translation'] || 
                                'No description available.';
            console.log("Setting Translation provider description:", description);
            descriptionDiv.text(description);
        }

        function updateTTSProviderDescription(provider) {
            const descriptionDiv = setupDescriptionArea('#tts_provider_select', 'tts-provider-description');
            if (!descriptionDiv) return;
            
            const description = providerDescriptions[provider] || 
                                providerDescriptions[provider + '_tts'] || 
                                'No description available.';
            console.log("Setting TTS provider description:", description);
            descriptionDiv.text(description);
        }

        function updateLLMProviderDescription(provider) {
            const descriptionDiv = setupDescriptionArea('#llm_provider_select', 'llm-provider-description');
            if (!descriptionDiv) return;
            
            const description = providerDescriptions[provider] || 'No description available.';
            console.log("Setting LLM provider description:", description);
            descriptionDiv.text(description);
        }

        // Function to update temperature description
        function updateTemperatureDescription(temperature) {
            const descriptionDiv = setupDescriptionArea('#temperature_input', 'temperature-description');
            if (!descriptionDiv) return;
            
            // Round to nearest tenth for comparison
            const roundedTemp = Math.round(temperature * 10) / 10;
            // Find the closest predefined temperature
            let closestTemp = '0.7'; // default
            let minDiff = 2; // larger than max possible difference
            
            for (const temp in temperatureDescriptions) {
                const diff = Math.abs(parseFloat(temp) - roundedTemp);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestTemp = temp;
                }
            }
            
            const description = temperatureDescriptions[closestTemp] || 'Custom temperature value.';
            console.log("Setting temperature description:", description);
            descriptionDiv.text(description);
        }

        // Store initial values from the form when the page loads
        function storeInitialValues() {
            console.log("Storing initial values from the form");
            
            // Store STT values
            const sttModelVersionField = $('#stt_model_version_select');
            if (sttModelVersionField.length > 0) {
                const initialValue = sttModelVersionField.val();
                if (initialValue) {
                    console.log(`Setting initial value for STT model version: ${initialValue}`);
                    sttModelVersionField.attr('data-initial-value', initialValue);
                }
            }
            
            // Store Translation values
            const translationModelVersionField = $('#translation_model_version_select');
            if (translationModelVersionField.length > 0) {
                const initialValue = translationModelVersionField.val();
                if (initialValue) {
                    console.log(`Setting initial value for Translation model version: ${initialValue}`);
                    translationModelVersionField.attr('data-initial-value', initialValue);
                }
            }
            
            // Store TTS values
            const ttsModelVersionField = $('#tts_model_version_select');
            if (ttsModelVersionField.length > 0) {
                const initialValue = ttsModelVersionField.val();
                if (initialValue) {
                    console.log(`Setting initial value for TTS model version: ${initialValue}`);
                    ttsModelVersionField.attr('data-initial-value', initialValue);
                }
            }
            
            const ttsVoiceField = $('#tts_voice_select');
            if (ttsVoiceField.length > 0) {
                const initialValue = ttsVoiceField.val();
                if (initialValue) {
                    console.log(`Setting initial value for TTS voice: ${initialValue}`);
                    ttsVoiceField.attr('data-initial-value', initialValue);
                }
            }
            
            // Store LLM values
            const llmModelVersionField = $('#llm_model_version_select');
            if (llmModelVersionField.length > 0) {
                const initialValue = llmModelVersionField.val();
                if (initialValue) {
                    console.log(`Setting initial value for LLM model version: ${initialValue}`);
                    llmModelVersionField.attr('data-initial-value', initialValue);
                }
            }
        }

        // Setup event handlers
        function setupEventHandlers() {
             // First store initial values
             storeInitialValues();

            // STT Provider change handler
            $('#stt_provider_select').change(function() {
                const provider = $(this).val();
                console.log("STT Provider changed to:", provider);
                updateSTTModelVersionOptions(provider);
                updateSTTProviderDescription(provider);
            });
            
            // Translation Provider change handler
            $('#translation_provider_select').change(function() {
                const provider = $(this).val();
                console.log("Translation Provider changed to:", provider);
                updateTranslationModelVersionOptions(provider);
                updateTranslationProviderDescription(provider);
            });
            
            // TTS Provider change handler
            $('#tts_provider_select').change(function() {
                const provider = $(this).val();
                console.log("TTS Provider changed to:", provider);
                updateTTSOptions(provider);
                updateTTSProviderDescription(provider);
            });
            
            // LLM Provider change handler
            $('#llm_provider_select').change(function() {
                const provider = $(this).val();
                console.log("LLM Provider changed to:", provider);
                updateLLMModelVersionOptions(provider);
                updateLLMProviderDescription(provider);
            });
            
            // Temperature change handler
            $('#temperature_input').on('input change', function() {
                const temperature = parseFloat($(this).val());
                console.log("Temperature changed to:", temperature);
                updateTemperatureDescription(temperature);
            });
            
            // Trigger initial updates
            const sttProvider = $('#stt_provider_select').val();
            console.log("STT Provider value:", sttProvider); 
            if (sttProvider) {
                const sttModelVersionElement = $('#stt_model_version_select');

                if (sttModelVersionElement.length > 0) {
                    const sttModelVersion = sttModelVersionElement.val();
                    console.log("hello3");

                    if (!sttModelVersion) {
                        console.log("Entered");
                        updateSTTModelVersionOptions(sttProvider);
                    }
                } else {
                    console.log("STT model version select element not found.");
                    updateSTTModelVersionOptions(sttProvider);
                }

                updateSTTProviderDescription(sttProvider);
            }
            else {
                console.log("Nothing there");
            }
            
            const translationProvider = $('#translation_provider_select').val();
            if (translationProvider) {
                updateTranslationModelVersionOptions(translationProvider);
                updateTranslationProviderDescription(translationProvider);
            }
            
            const ttsProvider = $('#tts_provider_select').val();
            if (ttsProvider) {
                updateTTSOptions(ttsProvider);
                updateTTSProviderDescription(ttsProvider);
            }
            
            const llmProvider = $('#llm_provider_select').val();
            if (llmProvider) {
                updateLLMModelVersionOptions(llmProvider);
                updateLLMProviderDescription(llmProvider);
            }
            
            const temperature = parseFloat($('#temperature_input').val());
            if (!isNaN(temperature)) {
                updateTemperatureDescription(temperature);
            }
        }

        // Call setup after a short delay to ensure all elements are loaded
        setTimeout(setupEventHandlers, 500);
    });
})(django.jQuery || jQuery);