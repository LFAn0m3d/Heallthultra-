import React from 'react';
import { RouteProp, useRoute } from '@react-navigation/native';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { RootStackParamList } from '../app/App';
import { AnalyzeResponse } from '../services/api';

export interface ResultScreenParams {
  result: AnalyzeResponse;
}

type ResultRoute = RouteProp<RootStackParamList, 'Result'>;

const ResultScreen: React.FC = () => {
  const route = useRoute<ResultRoute>();
  const { result } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.triageLabel}>ระดับคัดกรอง: {result.triage_level}</Text>
      <Text style={styles.sectionTitle}>เหตุผล</Text>
      <FlatList
        data={result.rationale}
        keyExtractor={(item, index) => `rationale-${index}`}
        renderItem={({ item }) => <Text style={styles.listItem}>• {item}</Text>}
      />
      <Text style={styles.sectionTitle}>การดำเนินการแนะนำ</Text>
      <FlatList
        data={result.actions}
        keyExtractor={(item, index) => `action-${index}`}
        renderItem={({ item }) => <Text style={styles.listItem}>• {item}</Text>}
      />
      {result.condition_hints.length > 0 && (
        <View>
          <Text style={styles.sectionTitle}>เฝ้าระวังเพิ่มเติม</Text>
          {result.condition_hints.map((hint, index) => (
            <Text key={`hint-${index}`} style={styles.listItem}>
              • {hint}
            </Text>
          ))}
        </View>
      )}
      <Text style={styles.warning}>
        ผลลัพธ์นี้ไม่ใช่การวินิจฉัย หากมีอาการรุนแรงให้ไปโรงพยาบาลทันที
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    backgroundColor: '#fff',
    gap: 16,
  },
  triageLabel: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1e40af',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
  },
  listItem: {
    fontSize: 16,
    marginVertical: 4,
  },
  warning: {
    marginTop: 24,
    color: '#c53030',
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default ResultScreen;
