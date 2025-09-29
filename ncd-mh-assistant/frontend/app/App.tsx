import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from '../screens/HomeScreen';
import IntakeScreen from '../screens/IntakeScreen';
import ResultScreen, { ResultScreenParams } from '../screens/ResultScreen';
import TrendsScreen from '../screens/TrendsScreen';

export type RootStackParamList = {
  Home: undefined;
  Intake: undefined;
  Result: ResultScreenParams;
  Trends: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'NCD/MH Assistant' }} />
        <Stack.Screen name="Intake" component={IntakeScreen} options={{ title: 'Intake' }} />
        <Stack.Screen name="Result" component={ResultScreen} options={{ title: 'Result' }} />
        <Stack.Screen name="Trends" component={TrendsScreen} options={{ title: 'Trends' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
