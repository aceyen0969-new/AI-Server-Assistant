#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <fstream>
#include <set>
#include <algorithm>
#include <cctype>

struct LanguageSegment {
    std::string language;
    std::vector<std::string> words;
};

std::string normalize(
    const std::string& text
) {
    std::string result;

    for (unsigned char character : text) {
        if (std::isalnum(character)) {
            result += static_cast<char>(
                std::tolower(character)
            );
        }
        else if (
            std::isspace(character) ||
            character == '-'
        ) {
            result += ' ';
        }
    }

    return result;
}

std::vector<std::string> tokenize(
    const std::string& text
) {
    std::vector<std::string> words;

    std::stringstream stream(
        normalize(text)
    );

    std::string word;

    while (stream >> word) {
        words.push_back(word);
    }

    return words;
}

std::vector<std::string> build_trigrams(
    const std::string& word
) {
    std::vector<std::string> trigrams;

    if (word.length() < 3) {
        return trigrams;
    }

    for (
        std::size_t i = 0;
        i + 2 < word.length();
        ++i
    ) {
        trigrams.push_back(
            word.substr(i, 3)
        );
    }

    return trigrams;
}

std::map<std::string, double> build_profile(
    const std::string& filename
) {
    std::map<std::string, double> profile;
    std::ifstream file(filename);

    if (!file.is_open()) {
        return profile;
    }

    std::string line;
    int total_trigrams = 0;

    while (std::getline(file, line)) {
        std::vector<std::string> words =
            tokenize(line);

        for (const std::string& word : words) {
            std::vector<std::string> trigrams =
                build_trigrams(word);

            for (const std::string& trigram : trigrams) {
                profile[trigram]++;
                total_trigrams++;
            }
        }
    }

    if (total_trigrams == 0) {
        return profile;
    }

    for (
        auto& entry : profile
    ) {
        entry.second /=
            static_cast<double>(
                total_trigrams
            );
    }

    return profile;
}

void merge_profile(
    std::map<std::string, double>& profile,
    const std::map<std::string, double>& additional
) {
    for (const auto& entry : additional) {
        profile[entry.first] += entry.second;
    }

    double total = 0.0;

    for (const auto& entry : profile) {
        total += entry.second;
    }

    if (total <= 0.0) {
        return;
    }

    for (auto& entry : profile) {
        entry.second /= total;
    }
}

std::set<std::string> build_vocabulary(
    const std::string& filename
) {
    std::set<std::string> vocabulary;

    std::ifstream file(
        filename
    );

    if (!file.is_open()) {
        return vocabulary;
    }

    std::string line;

    while (std::getline(file, line)) {
        std::vector<std::string> words =
            tokenize(line);

        for (const std::string& word : words) {
            vocabulary.insert(word);
        }
    }

    return vocabulary;
}

void merge_vocabulary(
    std::set<std::string>& vocabulary,
    const std::string& filename
) {
    std::set<std::string> additional =
        build_vocabulary(filename);

    vocabulary.insert(
        additional.begin(),
        additional.end()
    );
}

int count_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary
) {
    int score = 0;

    for (const std::string& word : words) {
        if (
            vocabulary.find(word)
            != vocabulary.end()
        ) {
            score++;
        }
    }

    return score;
}

int count_unique_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary,
    const std::set<std::string>& other_vocabulary_1,
    const std::set<std::string>& other_vocabulary_2
) {
    int score = 0;

    for (const std::string& word : words) {
        if (
            vocabulary.find(word)
                != vocabulary.end() &&
            other_vocabulary_1.find(word)
                == other_vocabulary_1.end() &&
            other_vocabulary_2.find(word)
                == other_vocabulary_2.end()
        ) {
            score++;
        }
    }

    return score;
}

double calculate_trigram_score(
    const std::vector<std::string>& trigrams,
    const std::map<std::string, double>& profile
) {
    if (trigrams.empty()) {
        return 0.0;
    }

    double score = 0.0;

    for (const std::string& trigram : trigrams) {
        auto iterator =
            profile.find(trigram);

        if (
            iterator != profile.end()
        ) {
            score += iterator->second;
        }
    }

    return score;
}

double calculate_score_margin(
    double english_score,
    double filipino_score,
    double bisaya_score
) {
    std::vector<double> scores = {
        english_score,
        filipino_score,
        bisaya_score
    };

    std::sort(
        scores.begin(),
        scores.end(),
        std::greater<double>()
    );

    return scores[0] - scores[1];
}

bool detect_code_switch(
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score
) {
    int language_count = 0;

    if (english_unique_score >= 1) {
        language_count++;
    }

    if (filipino_unique_score >= 1) {
        language_count++;
    }

    if (bisaya_unique_score >= 1) {
        language_count++;
    }

    return language_count >= 2;
}

std::string word_language(
    const std::string& word,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    bool english =
        english_vocabulary.find(word)
        != english_vocabulary.end();

    bool filipino =
        filipino_vocabulary.find(word)
        != filipino_vocabulary.end();

    bool bisaya =
        bisaya_vocabulary.find(word)
        != bisaya_vocabulary.end();

    int matches =
        static_cast<int>(english) +
        static_cast<int>(filipino) +
        static_cast<int>(bisaya);

    if (matches == 1) {
        if (english) {
            return "english";
        }

        if (filipino) {
            return "filipino";
        }

        return "bisaya";
    }

    std::vector<std::string> trigrams =
        build_trigrams(word);

    if (trigrams.empty()) {
        return "unknown";
    }

    double english_score =
        calculate_trigram_score(
            trigrams,
            english_profile
        );

    double filipino_score =
        calculate_trigram_score(
            trigrams,
            filipino_profile
        );

    double bisaya_score =
        calculate_trigram_score(
            trigrams,
            bisaya_profile
        );

    double highest_score =
        std::max({
            english_score,
            filipino_score,
            bisaya_score
        });

    if (highest_score <= 0.0) {
        return "unknown";
    }

    std::vector<double> scores = {
        english_score,
        filipino_score,
        bisaya_score
    };

    std::sort(
        scores.begin(),
        scores.end(),
        std::greater<double>()
    );

    double second_highest_score =
        scores[1];

    double relative_margin =
        highest_score > 0.0
            ? (
                highest_score -
                second_highest_score
            ) / highest_score
            : 0.0;

    const double minimum_confidence =
        0.20;

    const double minimum_margin =
        0.10;

    double confidence =
        highest_score /
        (
            english_score +
            filipino_score +
            bisaya_score
        );

    if (
        confidence < minimum_confidence ||
        relative_margin < minimum_margin
    ) {
        return "shared";
    }

    if (
        english_score >= filipino_score &&
        english_score >= bisaya_score
    ) {
        return "english";
    }

    if (
        filipino_score >= english_score &&
        filipino_score >= bisaya_score
    ) {
        return "filipino";
    }

    return "bisaya";
}

std::vector<LanguageSegment> build_language_segments(
    const std::vector<std::string>& words,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    std::vector<LanguageSegment> segments;

    std::string current_language;

    for (const std::string& word : words) {
        std::string language =
            word_language(
                word,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                english_profile,
                filipino_profile,
                bisaya_profile
            );

        if (
            language == "unknown" ||
            language == "shared"
        ) {
            continue;
        }

        if (
            segments.empty() ||
            language != current_language
        ) {
            LanguageSegment segment;

            segment.language =
                language;

            segment.words.push_back(
                word
            );

            segments.push_back(
                segment
            );

            current_language =
                language;
        }
        else {
            segments.back().words.push_back(
                word
            );
        }
    }

    return segments;
}

int count_language_switches(
    const std::vector<LanguageSegment>& segments
) {
    if (segments.size() <= 1) {
        return 0;
    }

    return static_cast<int>(
        segments.size() - 1
    );
}

std::string build_switch_direction(
    const std::vector<LanguageSegment>& segments
) {
    if (segments.empty()) {
        return "";
    }

    std::string result =
        segments[0].language;

    for (
        std::size_t i = 1;
        i < segments.size();
        ++i
    ) {
        result += "->";
        result += segments[i].language;
    }

    return result;
}

std::string escape_json(
    const std::string& text
) {
    std::string result;

    for (char character : text) {
        switch (character) {
            case '"':
                result += "\\\"";
                break;

            case '\\':
                result += "\\\\";
                break;

            case '\n':
                result += "\\n";
                break;

            case '\r':
                result += "\\r";
                break;

            case '\t':
                result += "\\t";
                break;

            default:
                result += character;
                break;
        }
    }

    return result;
}

void print_json(
    const std::string& language,
    bool mixed,
    bool code_switched,
    bool ambiguous,
    double confidence,
    double score_margin,
    int switch_count,
    const std::string& code_switch_direction,
    int english_word_score,
    int filipino_word_score,
    int bisaya_word_score,
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score,
    double english_trigram_score,
    double filipino_trigram_score,
    double bisaya_trigram_score,
    const std::vector<LanguageSegment>& segments
) {
    std::cout << "{\n";

    std::cout
        << "  \"language\": \""
        << escape_json(language)
        << "\",\n";

    std::cout
        << "  \"mixed\": "
        << (mixed ? "true" : "false")
        << ",\n";

    std::cout
        << "  \"code_switched\": "
        << (code_switched ? "true" : "false")
        << ",\n";

    std::cout
        << "  \"ambiguous\": "
        << (ambiguous ? "true" : "false")
        << ",\n";

    std::cout
        << "  \"confidence\": "
        << confidence
        << ",\n";

    std::cout
        << "  \"score_margin\": "
        << score_margin
        << ",\n";

    std::cout
        << "  \"switch_count\": "
        << switch_count
        << ",\n";

    std::cout
        << "  \"code_switch_direction\": \""
        << escape_json(
            code_switch_direction
        )
        << "\",\n";

    std::cout
        << "  \"english_word_score\": "
        << english_word_score
        << ",\n";

    std::cout
        << "  \"filipino_word_score\": "
        << filipino_word_score
        << ",\n";

    std::cout
        << "  \"bisaya_word_score\": "
        << bisaya_word_score
        << ",\n";

    std::cout
        << "  \"english_unique_score\": "
        << english_unique_score
        << ",\n";

    std::cout
        << "  \"filipino_unique_score\": "
        << filipino_unique_score
        << ",\n";

    std::cout
        << "  \"bisaya_unique_score\": "
        << bisaya_unique_score
        << ",\n";

    std::cout
        << "  \"english_trigram_score\": "
        << english_trigram_score
        << ",\n";

    std::cout
        << "  \"filipino_trigram_score\": "
        << filipino_trigram_score
        << ",\n";

    std::cout
        << "  \"bisaya_trigram_score\": "
        << bisaya_trigram_score
        << ",\n";

    std::cout
        << "  \"segments\": [\n";

    for (
        std::size_t i = 0;
        i < segments.size();
        ++i
    ) {
        const LanguageSegment& segment =
            segments[i];

        std::cout
            << "    {\n";

        std::cout
            << "      \"language\": \""
            << escape_json(
                segment.language
            )
            << "\",\n";

        std::cout
            << "      \"words\": \"";

        for (
            std::size_t j = 0;
            j < segment.words.size();
            ++j
        ) {
            if (j > 0) {
                std::cout << " ";
            }

            std::cout
                << escape_json(
                    segment.words[j]
                );
        }

        std::cout
            << "\"\n";

        std::cout
            << "    }";

        if (
            i + 1 <
            segments.size()
        ) {
            std::cout << ",";
        }

        std::cout << "\n";
    }

    std::cout
        << "  ]\n";

    std::cout
        << "}\n";
}

int main() {
    const std::string english_training =
        "training/english.txt";

    const std::string filipino_training =
        "training/filipino.txt";

    const std::string bisaya_training =
        "training/bisaya.txt";

    const std::string english_learned =
        "training/learned/english.txt";

    const std::string filipino_learned =
        "training/learned/filipino.txt";

    const std::string bisaya_learned =
        "training/learned/bisaya.txt";

    std::map<std::string, double> english_profile =
        build_profile(
            english_training
        );

    std::map<std::string, double> filipino_profile =
        build_profile(
            filipino_training
        );

    std::map<std::string, double> bisaya_profile =
        build_profile(
            bisaya_training
        );

    merge_profile(
        english_profile,
        build_profile(
            english_learned
        )
    );

    merge_profile(
        filipino_profile,
        build_profile(
            filipino_learned
        )
    );

    merge_profile(
        bisaya_profile,
        build_profile(
            bisaya_learned
        )
    );

    std::set<std::string> english_vocabulary =
        build_vocabulary(
            english_training
        );

    std::set<std::string> filipino_vocabulary =
        build_vocabulary(
            filipino_training
        );

    std::set<std::string> bisaya_vocabulary =
        build_vocabulary(
            bisaya_training
        );

    merge_vocabulary(
        english_vocabulary,
        english_learned
    );

    merge_vocabulary(
        filipino_vocabulary,
        filipino_learned
    );

    merge_vocabulary(
        bisaya_vocabulary,
        bisaya_learned
    );

    std::cout
        << "Quasar Language Engine v0.7.2\n";

    std::cout
        << "English vocabulary: "
        << english_vocabulary.size()
        << "\n";

    std::cout
        << "Filipino vocabulary: "
        << filipino_vocabulary.size()
        << "\n";

    std::cout
        << "Bisaya vocabulary: "
        << bisaya_vocabulary.size()
        << "\n";

    std::cout
        << "Learned vocabulary enabled.\n";

    std::cout
        << "Enter a message:\n";

    std::string message;

    while (
        std::getline(
            std::cin,
            message
        )
    ) {
        if (message.empty()) {
            continue;
        }

        std::vector<std::string> words =
            tokenize(message);

        int english_word_score =
            count_vocabulary_matches(
                words,
                english_vocabulary
            );

        int filipino_word_score =
            count_vocabulary_matches(
                words,
                filipino_vocabulary
            );

        int bisaya_word_score =
            count_vocabulary_matches(
                words,
                bisaya_vocabulary
            );

        int english_unique_score =
            count_unique_vocabulary_matches(
                words,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary
            );

        int filipino_unique_score =
            count_unique_vocabulary_matches(
                words,
                filipino_vocabulary,
                english_vocabulary,
                bisaya_vocabulary
            );

        int bisaya_unique_score =
            count_unique_vocabulary_matches(
                words,
                bisaya_vocabulary,
                english_vocabulary,
                filipino_vocabulary
            );

        std::vector<std::string> message_trigrams =
            build_trigrams(
                normalize(message)
            );

        double english_trigram_score =
            calculate_trigram_score(
                message_trigrams,
                english_profile
            );

        double filipino_trigram_score =
            calculate_trigram_score(
                message_trigrams,
                filipino_profile
            );

        double bisaya_trigram_score =
            calculate_trigram_score(
                message_trigrams,
                bisaya_profile
            );

        double english_total =
            english_unique_score +
            english_trigram_score;

        double filipino_total =
            filipino_unique_score +
            filipino_trigram_score;

        double bisaya_total =
            bisaya_unique_score +
            bisaya_trigram_score;

        double total_score =
            english_total +
            filipino_total +
            bisaya_total;

        double highest_score =
            std::max({
                english_total,
                filipino_total,
                bisaya_total
            });

        double score_margin =
            calculate_score_margin(
                english_total,
                filipino_total,
                bisaya_total
            );

        const double ambiguity_threshold =
            0.1;

        std::string language =
            "unknown";

        bool mixed = false;
        bool ambiguous = false;

        double confidence = 0.0;

        int strong_language_count = 0;

        if (
            english_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            filipino_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            bisaya_word_score >= 2
        ) {
            strong_language_count++;
        }

        if (
            strong_language_count < 2
        ) {
            if (
                english_word_score >= 1 &&
                filipino_word_score >= 1
            ) {
                strong_language_count = 2;
            }

            if (
                english_word_score >= 1 &&
                bisaya_word_score >= 1
            ) {
                strong_language_count = 2;
            }

            if (
                filipino_word_score >= 1 &&
                bisaya_word_score >= 1
            ) {
                strong_language_count = 2;
            }
        }

        if (
            strong_language_count >= 2
        ) {
            mixed = true;

            if (
                english_total >= filipino_total &&
                english_total >= bisaya_total
            ) {
                language = "taglish";
            }
            else if (
                filipino_total >= english_total &&
                filipino_total >= bisaya_total
            ) {
                language = "taglish";
            }
            else {
                language = "mixed";
            }
        }
        else if (
            total_score > 0
        ) {
            if (
                score_margin <
                ambiguity_threshold
            ) {
                language = "ambiguous";
                ambiguous = true;
            }
            else if (
                english_total >= filipino_total &&
                english_total >= bisaya_total
            ) {
                language = "english";
            }
            else if (
                filipino_total >= english_total &&
                filipino_total >= bisaya_total
            ) {
                language = "filipino";
            }
            else {
                language = "bisaya";
            }

            confidence =
                highest_score /
                total_score;
        }

        bool code_switched =
            detect_code_switch(
                english_unique_score,
                filipino_unique_score,
                bisaya_unique_score
            );

        std::vector<LanguageSegment> segments =
            build_language_segments(
                words,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                english_profile,
                filipino_profile,
                bisaya_profile
            );

        int switch_count =
            count_language_switches(
                segments
            );

        std::string code_switch_direction =
            build_switch_direction(
                segments
            );

        print_json(
            language,
            mixed,
            code_switched,
            ambiguous,
            confidence,
            score_margin,
            switch_count,
            code_switch_direction,
            english_word_score,
            filipino_word_score,
            bisaya_word_score,
            english_unique_score,
            filipino_unique_score,
            bisaya_unique_score,
            english_trigram_score,
            filipino_trigram_score,
            bisaya_trigram_score,
            segments
        );

        std::cout
            << "Enter a message:\n";
    }

    return 0;
}