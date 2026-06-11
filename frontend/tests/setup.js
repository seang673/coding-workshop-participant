import '@testing-library/jest-dom'
import React from 'react'
import { vi } from 'vitest'

function passthrough(tag) {
	return ({ children, ...props }) => React.createElement(tag, props, children)
}

vi.mock('@mui/material', () => {
	const Box = ({ component, children, ...props }) => {
		const tag = component || 'div'
		return React.createElement(tag, props, children)
	}

	const Button = ({ children, component, to, ...props }) => {
		if (component && to) {
			return React.createElement('a', { href: to, ...props }, children)
		}
		return React.createElement('button', props, children)
	}

	const TextField = ({ label, helperText, select, children, value, onChange, ...props }) => {
		if (select) {
			return React.createElement(
				'label',
				null,
				label,
				React.createElement('select', { 'aria-label': label, value, onChange, ...props }, children),
				helperText ? React.createElement('small', null, helperText) : null,
			)
		}

		return React.createElement(
			'label',
			null,
			label,
			React.createElement('input', { 'aria-label': label, value, onChange, ...props }),
			helperText ? React.createElement('small', null, helperText) : null,
		)
	}

	const Link = ({ component, to, children, ...props }) => {
		if (component && to) {
			return React.createElement('a', { href: to, ...props }, children)
		}
		return React.createElement('a', props, children)
	}

	return {
		Box,
		Button,
		Paper: passthrough('section'),
		Stack: passthrough('div'),
		Typography: passthrough('p'),
		Alert: passthrough('div'),
		TextField,
		Link,
		MenuItem: ({ value, children }) => React.createElement('option', { value }, children),
	}
})
