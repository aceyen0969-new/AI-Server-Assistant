#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <fstream>
#include <set>
#include <algorithm>
#include <cctype>

std::string normalize(
    const std::string& text
) {
    std::string result;

    for (char c : text) {

        if (
            std::isalnum(
                static_cast<unsigned char>(c)
            )
        ) {
            result += static_cast<char>(
                std::tolower(
                    static_cast<unsigned char>(c)
                )
            );
        }
        else {
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
    const std::string& text
) {
    std::vector<std::string> trigrams;

    std::string normalized =
        normalize(text);

    for (
        std::size_t i = 0;
        i + 2 < normalized.size();
        ++i
    ) {
        if (
            normalized[i] == ' ' ||
            normalized[i + 1] == ' ' ||
            normalized[i + 2] == ' '
        ) {
            continue;
        }

        trigrams.push_back(
            normalized.substr(i, 3)
        );
    }

    return trigrams;
}

std::map<std::string, int> build_profile(
    const std::string& filename
) {
    std::map<std::string, int> profile;

    std::ifstream file(
        filename
    );

    if (!file.is_open()) {
        std::cerr
            << "Could not open training file: "
            << filename
            << std::endl;

        return profile;
    }

    std::string line;

    while (std::getline(file, line)) {

        std::vector<std::string> trigrams =
            build_trigrams(line);

        for (
            const std::string& trigram :
            trigrams
        ) {
            profile[trigram]++;
        }
    }

    return profile;
}

std::map<std::string, double> normalize_profile(
    const std::map<std::string, int>& profile
) {
    std::map<std::string, double> normalized;

    int total = 0;

    for (
        const auto& entry :
        profile
    ) {
        total += entry.second;
    }

    if (total == 0) {
        return normalized;
    }

    for (
        const auto& entry :
        profile
    ) {
        normalized[entry.first] =
            static_cast<double>(
                entry.second
            ) / total;
    }

    return normalized;
}

std::set<std::string> build_vocabulary(
    const std::string& filename
) {
    std::set<std::string> vocabulary;

    std::ifstream file(
        filename
    );

    if (!file.is_open()) {
        std::cerr
            << "Could not open vocabulary file: "
            << filename
            << std::endl;

        return vocabulary;
    }

    std::string line;

    while (std::getline(file, line)) {

        std::vector<std::string> words =
            tokenize(line);

        for (
            const std::string& word :
            words
        ) {
            if (!word.empty()) {
                vocabulary.insert(word);
            }
        }
    }

    return vocabulary;
}

int count_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary
) {
    int score = 0;

    for (
        const std::string& word :
        words
    ) {
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

    for (
        const std::string& word :
        words
    ) {
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

bool detect_code_switch(
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score
) {
    int language_count = 0;

    if (
        english_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        filipino_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        bisaya_unique_score >= 1
    ) {
        language_count++;
    }

    return language_count >= 2;
}

double calculate_trigram_score(
    const std::vector<std::string>& trigrams,
    const std::map<std::string, double>& profile
) {
    if (trigrams.empty()) {
        return 0.0;
    }

    double score = 0.0;

    for (
        const std::string& trigram :
        trigrams
    ) {
        auto found =
            profile.find(trigram);

        if (
            found != profile.end()
        ) {
            score += found->second;
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

int main() {

    std::cout
        << "Quasar Language Engine v0.7.0"
        << std::endl;

    std::map<std::string, int> english_profile =
        build_profile(
            "training/english.txt"
        );

    std::map<std::string, int> filipino_profile =
        build_profile(
            "training/filipino.txt"
        );

    std::map<std::string, int> bisaya_profile =
        build_profile(
            "training/bisaya.txt"
        );

    std::map<std::string, double> english_normalized =
        normalize_profile(
            english_profile
        );

    std::map<std::string, double> filipino_normalized =
        normalize_profile(
            filipino_profile
        );

    std::map<std::string, double> bisaya_normalized =
        normalize_profile(
            bisaya_profile
        );

    std::set<std::string> english_vocabulary =
        build_vocabulary(
            "training/english.txt"
        );

    std::set<std::string> filipino_vocabulary =
        build_vocabulary(
            "training/filipino.txt"
        );

    std::set<std::string> bisaya_vocabulary =
        build_vocabulary(
            "training/bisaya.txt"
        );

    std::cout
        << "English trigrams: "
        << english_profile.size()
        << std::endl;

    std::cout
        << "Filipino trigrams: "
        << filipino_profile.size()
        << std::endl;

    std::cout
        << "Bisaya trigrams: "
        << bisaya_profile.size()
        << std::endl;

    std::cout
        << "English vocabulary: "
        << english_vocabulary.size()
        << std::endl;

    std::cout
        << "Filipino vocabulary: "
        << filipino_vocabulary.size()
        << std::endl;

    std::cout
        << "Bisaya vocabulary: "
        << bisaya_vocabulary.size()
        << std::endl;

    const double ambiguity_threshold = 0.1;

    while (true) {

        std::cout
            << "\nEnter a message: ";

        std::string message;

        if (!std::getline(
            std::cin,
            message
        )) {
            break;
        }

        if (message.empty()) {
            continue;
        }

        std::vector<std::string> words =
            tokenize(message);

        std::vector<std::string> trigrams =
            build_trigrams(message);

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

        double english_trigram_score =
            calculate_trigram_score(
                trigrams,
                english_normalized
            );

        double filipino_trigram_score =
            calculate_trigram_score(
                trigrams,
                filipino_normalized
            );

        double bisaya_trigram_score =
            calculate_trigram_score(
                trigrams,
                bisaya_normalized
            );

        double english_total =
            english_word_score
            + english_trigram_score;

        double filipino_total =
            filipino_word_score
            + filipino_trigram_score;

        double bisaya_total =
            bisaya_word_score
            + bisaya_trigram_score;

        double total_score =
            english_total
            + filipino_total
            + bisaya_total;

        double score_margin =
            calculate_score_margin(
                english_total,
                filipino_total,
                bisaya_total
            );

        std::string language =
            "unknown";

        bool mixed = false;

        bool ambiguous = false;

        double confidence = 0.0;

        bool code_switched =
            detect_code_switch(
                english_unique_score,
                filipino_unique_score,
                bisaya_unique_score
            );

        int strong_language_count = 0;

        if (
            english_unique_score >= 1
        ) {
            strong_language_count++;
        }

        if (
            filipino_unique_score >= 1
        ) {
            strong_language_count++;
        }

        if (
            bisaya_unique_score >= 1
        ) {
            strong_language_count++;
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
                score_margin < ambiguity_threshold
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

            double highest_score =
                std::max({
                    english_total,
                    filipino_total,
                    bisaya_total
                });

            confidence =
                highest_score / total_score;
        }

        if (
            mixed &&
            total_score > 0
        ) {

            double highest_score =
                std::max({
                    english_total,
                    filipino_total,
                    bisaya_total
                });

            confidence =
                highest_score / total_score;
        }

        std::cout
            << "{"
            << "\"language\":\""
            << language
            << "\","
            << "\"mixed\":"
            << (mixed ? "true" : "false")
            << ","
            << "\"code_switched\":"
            << (code_switched ? "true" : "false")
            << ","
            << "\"ambiguous\":"
            << (ambiguous ? "true" : "false")
            << ","
            << "\"confidence\":"
            << confidence
            << ","
            << "\"score_margin\":"
            << score_margin
            << ","
            << "\"english_word_score\":"
            << english_word_score
            << ","
            << "\"filipino_word_score\":"
            << filipino_word_score
            << ","
            << "\"bisaya_word_score\":"
            << bisaya_word_score
            << ","
            << "\"english_unique_score\":"
            << english_unique_score
            << ","
            << "\"filipino_unique_score\":"
            << filipino_unique_score
            << ","
            << "\"bisaya_unique_score\":"
            << bisaya_unique_score
            << ","
            << "\"english_trigram_score\":"
            << english_trigram_score
            << ","
            << "\"filipino_trigram_score\":"
            << filipino_trigram_score
            << ","
            << "\"bisaya_trigram_score\":"
            << bisaya_trigram_score
            << "}"
            << std::endl;
    }

    return 0;
}